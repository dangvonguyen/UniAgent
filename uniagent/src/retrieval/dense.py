from __future__ import annotations

import asyncio
import hashlib
import os
import time
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

from src.config import (
    DENSE_BATCH_SIZE,
    DENSE_MODEL,
    EMBEDDING_CACHE_DIR,
    RETRIEVAL_DEPTH,
)

from .corpora import PreparedCorpus
from .fusion import SearchHit
from .passages import Passage

Embeddings = NDArray[np.float32]


class DenseEncoder:
    """Turns text into unit-length vectors."""

    def __init__(self, model_name: str = DENSE_MODEL) -> None:
        self.model_name = model_name
        print(f"Loading dense encoder {model_name}...", flush=True)
        start = time.perf_counter()
        self._model = SentenceTransformer(model_name, device="cpu")
        print(f"Dense encoder loaded in {time.perf_counter() - start:.2f}s", flush=True)

    def encode(self, texts: list[str]) -> Embeddings:
        """One row per text. Rows have length 1, so a dot product equals cosine."""
        return self._model.encode(
            texts,
            batch_size=DENSE_BATCH_SIZE,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )


class DenseRetriever:
    """Embedding-based search over one corpus."""

    def __init__(
        self,
        corpus_name: str,
        passages: dict[str, Passage],
        language: str,
        encoder: DenseEncoder,
    ) -> None:
        if not passages:
            raise ValueError(f"Corpus {corpus_name!r} contains no passages.")

        self._corpus_name = corpus_name
        self._language = language
        self._passages = list(passages.values())

        self._cache_path = (EMBEDDING_CACHE_DIR / f"{corpus_name}.npz").resolve()
        self._embeddings = self._load_or_encode_passages(encoder)

    @property
    def language(self) -> str:
        return self._language

    def search(
        self, query_embedding: Embeddings, depth: int = RETRIEVAL_DEPTH
    ) -> list[SearchHit]:
        scores = self._embeddings @ query_embedding
        depth = min(depth, len(scores))

        top = np.argpartition(-scores, depth - 1)[:depth]
        top = top[np.argsort(-scores[top], kind="stable")]
        return [
            SearchHit(passage=self._passages[i], score=float(scores[i])) for i in top
        ]

    def _load_or_encode_passages(self, encoder: DenseEncoder) -> Embeddings:
        texts = [f"{passage.title}\n{passage.text}" for passage in self._passages]
        fingerprint = self._compute_fingerprint(encoder.model_name, texts)

        if self._cache_path.is_file():
            with np.load(self._cache_path) as cached:
                if str(cached["fingerprint"]) == fingerprint:
                    print(f"[{self._corpus_name}] reusing cached embeddings", flush=True)
                    return cached["embeddings"]

        start = time.perf_counter()
        embeddings = encoder.encode(texts)
        print(
            f"[{self._corpus_name}] encoded {len(self._passages)} passages "
            f"in {time.perf_counter() - start:.2f}s",
            flush=True,
        )

        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._cache_path.with_suffix(f".{os.getpid()}.tmp")
        with tmp_path.open("wb") as handle:
            np.savez(handle, fingerprint=np.array(fingerprint), embeddings=embeddings)
        # atomic, so an interrupted write is never treated as cached
        tmp_path.replace(self._cache_path)

        return embeddings

    @staticmethod
    def _compute_fingerprint(model_name: str, texts: list[str]) -> str:
        """Hash of everything that determines the embedding rows, in row order."""
        digest = hashlib.sha256(f"{model_name}\0".encode())
        for text in texts:
            digest.update(f"{text}\0".encode())
        return digest.hexdigest()


@dataclass(frozen=True)
class DenseIndex:
    """One shared encoder plus one dense retriever per corpus."""

    retrievers: dict[str, DenseRetriever]
    encoder: DenseEncoder

    @classmethod
    async def build(
        cls, corpora: dict[str, PreparedCorpus], names: list[str]
    ) -> DenseIndex:
        encoder = await asyncio.to_thread(DenseEncoder)
        retrievers: dict[str, DenseRetriever] = {}

        # One corpus at a time: encoding already uses every CPU thread.
        for name in names:
            corpus = corpora[name]
            retrievers[name] = await asyncio.to_thread(
                DenseRetriever, name, corpus.passages, corpus.language, encoder
            )
        return cls(retrievers, encoder)

    def search(
        self,
        questions: dict[str, list[str]],
        depth: int,
    ) -> list[list[SearchHit]]:
        """One ranked list per (corpus, question), matched by language."""
        pairs = [
            (retriever, question)
            for retriever in self.retrievers.values()
            for question in questions.get(retriever.language, [])
        ]
        if not pairs:
            return []

        # Encode all questions in one batch
        embeddings = self.encoder.encode([question for _, question in pairs])
        return [
            retriever.search(embedding, depth=depth)
            for (retriever, _), embedding in zip(pairs, embeddings, strict=True)
        ]
