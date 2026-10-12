from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
import threading
from dataclasses import dataclass

import pyterrier as pt

from src.config import (
    INDEX_CACHE_DIR,
    RETRIEVAL_DEPTH,
    RETRIEVAL_DOCNO_META_LENGTH,
    RETRIEVAL_WMODEL,
)

from .corpora import PreparedCorpus
from .fusion import SearchHit
from .languages import LANGUAGE_CONFIG
from .passages import Passage

# Terrier's underlying Java state is not thread-safe, so every Terrier call
# must hold this lock.
TERRIER_LOCK = threading.Lock()

_FINGERPRINT_FILENAME = "passages.sha256"


class LexicalRetriever:
    def __init__(
        self,
        corpus_name: str,
        passages: dict[str, Passage],
        language: str,
    ) -> None:
        if not passages:
            raise ValueError(f"Corpus {corpus_name!r} contains no passages.")

        self._corpus_name = corpus_name
        self._language = language
        self._passages = passages

        self._index_dir = (INDEX_CACHE_DIR / f"index-{corpus_name}").resolve()
        self._fingerprint_path = self._index_dir / _FINGERPRINT_FILENAME
        self._fingerprint = self._compute_fingerprint()

        # Create a retriever is not free, reuse one per (wmodel, depth)
        self._searchers: dict[tuple[str, int], pt.Transformer] = {}
        self._index = self._load_or_build_index()

    @property
    def language(self) -> str:
        return self._language

    def search(
        self,
        query: str,
        depth: int = RETRIEVAL_DEPTH,
        wmodel: str = RETRIEVAL_WMODEL,
    ) -> list[SearchHit]:
        with TERRIER_LOCK:
            results = self._get_searcher(wmodel, depth).search(query)

        return [
            SearchHit(
                passage=self._passages[row.docno],
                score=float(row.score),
            )
            for row in results.itertuples()
        ]

    def _get_searcher(self, wmodel: str, depth: int) -> pt.Transformer:
        key = (wmodel, depth)
        if key not in self._searchers:
            self._searchers[key] = self._index.retriever(wmodel, num_results=depth)
        return self._searchers[key]

    def _load_or_build_index(self) -> pt.terrier.TerrierIndex:
        with TERRIER_LOCK:
            if self._is_cache_valid():
                print(f"[{self._corpus_name}] reusing cached index")
                return pt.terrier.TerrierIndex(str(self._index_dir))

            print(f"[{self._corpus_name}] building index")
            if self._index_dir.exists():
                shutil.rmtree(self._index_dir)

            index = pt.terrier.TerrierIndex(str(self._index_dir))
            indexer = index.indexer(
                meta={"docno": RETRIEVAL_DOCNO_META_LENGTH},
                **LANGUAGE_CONFIG[self._language],
            )
            indexer.index(
                {
                    "docno": passage.passage_id,
                    "text": f"{passage.title}\n{passage.text}",
                }
                for passage in self._passages.values()
            )

            # written last, so an interrupted build is never treated as cached
            self._fingerprint_path.write_text(self._fingerprint)
            return index

    def _is_cache_valid(self) -> bool:
        return (
            self._fingerprint_path.is_file()
            and self._fingerprint_path.read_text().strip() == self._fingerprint
        )

    def _compute_fingerprint(self) -> str:
        """Hash of everything that determines index contents."""
        digest = hashlib.sha256()
        language_settings = json.dumps(
            LANGUAGE_CONFIG[self._language], sort_keys=True, default=str
        )
        digest.update(
            f"{self._language}\0{RETRIEVAL_DOCNO_META_LENGTH}\0{language_settings}\0".encode()
        )
        for passage in self._passages.values():
            digest.update(
                f"{passage.passage_id}\0{passage.title}\0{passage.text}\0".encode()
            )
        return digest.hexdigest()


@dataclass(frozen=True)
class LexicalIndex:
    """One BM25 retriever per corpus."""

    retrievers: dict[str, LexicalRetriever]

    @classmethod
    async def build(
        cls, corpora: dict[str, PreparedCorpus], names: list[str]
    ) -> LexicalIndex:
        # The global Terrier lock makes these run one after another for now.
        built = await asyncio.gather(
            *(
                asyncio.to_thread(
                    LexicalRetriever,
                    name,
                    corpora[name].passages,
                    corpora[name].language,
                )
                for name in names
            )
        )
        return cls(dict(zip(names, built, strict=True)))

    def search(
        self,
        queries: dict[str, list[str]],
        depth: int,
        wmodel: str = RETRIEVAL_WMODEL,
    ) -> list[list[SearchHit]]:
        return [
            retriever.search(query, depth=depth, wmodel=wmodel)
            for retriever in self.retrievers.values()
            for query in queries.get(retriever.language, [])
        ]
