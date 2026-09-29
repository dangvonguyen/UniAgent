from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
import shutil
import threading
import time
from collections import defaultdict
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, NamedTuple, TypedDict

import pyterrier as pt

from .config import (
    RETRIEVAL_DEPTH,
    RETRIEVAL_DOCNO_META_LENGTH,
    RETRIEVAL_RRF_K,
    RETRIEVAL_WMODEL,
)
from .passages import Passage, normalize_text, split_into_passages


class LanguageConfig(TypedDict):
    stemmer: pt.TerrierStemmer
    stopwords: pt.TerrierStopwords | list[str]
    tokeniser: pt.TerrierTokeniser


LANGUAGE_CONFIG: dict[str, LanguageConfig] = {
    "de": {
        "stemmer": pt.TerrierStemmer.german,
        "stopwords": (Path(__file__).parent.parent / "resources" / "german-stopwords.txt").read_text(encoding="utf-8").splitlines(),
        "tokeniser": pt.TerrierTokeniser.utf,
    },
    "en": {
        "stemmer": pt.TerrierStemmer.porter,
        "stopwords": pt.TerrierStopwords.terrier,
        "tokeniser": pt.TerrierTokeniser.english,
    },
}  # fmt: skip


Document = dict[str, Any]
CorpusDocuments = tuple[list[Passage], str]

# Terrier's underlying Java state is not thread-safe
_TERRIER_LOCK = threading.Lock()


class PreparedCorpus(NamedTuple):
    passages: dict[str, Passage]
    language: str


@dataclass(frozen=True)
class SearchHit:
    passage: Passage
    score: float


@dataclass(frozen=True)
class FusedHit:
    passage: Passage
    score: float

    @property
    def excerpt(self) -> str:
        return f"{self.passage.title}\n\n{self.passage.text}"


def fuse_by_reciprocal_rank(
    ranked_lists: Iterable[list[SearchHit]], *, rrf_k: int = RETRIEVAL_RRF_K
) -> list[FusedHit]:
    """Merge ranked result lists into one ranking, best first."""
    scores: dict[tuple[str, str], float] = defaultdict(float)
    passages: dict[tuple[str, str], Passage] = {}

    for hits in ranked_lists:
        for rank, hit in enumerate(hits, 1):
            key = (hit.passage.corpus, hit.passage.passage_id)
            scores[key] += 1.0 / (rrf_k + rank)
            passages.setdefault(key, hit.passage)

    return [
        FusedHit(passage=passages[key], score=scores[key])
        for key in sorted(scores, key=lambda key: (-scores[key], key))
    ]


def deduplicate_documents(documents: list[Document]) -> list[Document]:
    """Remove empty and exact-content duplicate documents before passage creation and indexing."""
    seen: set[str] = set()
    unique: list[Document] = []

    for document in documents:
        text = document.get("content", "")

        if not isinstance(text, str) or not text.strip():
            continue

        normalized = normalize_text(text)
        fingerprint = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

        if fingerprint in seen:
            continue

        seen.add(fingerprint)
        unique.append(document)

    return unique


def _validate_query(query: str) -> str:
    query = query.strip()
    if not query:
        raise ValueError("Query must not be empty.")
    return query


def _validate_num_results(num_results: int) -> None:
    if not 1 <= num_results <= 1000:
        raise ValueError("num_results must be between 1 and 1000.")


class CorpusRetriever:
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

        self._index_dir = Path(f"./runs/indices/index-{corpus_name}").resolve()
        self._index = self._build_index()

    def search(
        self,
        query: str,
        *,
        num_results: int = RETRIEVAL_DEPTH,
        wmodel: str = RETRIEVAL_WMODEL,
    ) -> list[SearchHit]:
        _validate_num_results(num_results)

        query = _validate_query(query)

        with _TERRIER_LOCK:
            retriever = self._index.retriever(wmodel, num_results=num_results)
            results = retriever.search(query)

        return [
            SearchHit(
                passage=self._passages[row.docno],
                score=float(row.score),
            )
            for row in results.itertuples()
        ]

    def _fingerprint(self) -> str:
        """Hash of everything that determines index contents."""
        digest = hashlib.sha256()
        digest.update(f"{self._language}\0{RETRIEVAL_DOCNO_META_LENGTH}\0".encode())
        for passage in self._passages.values():
            digest.update(
                f"{passage.passage_id}\0{passage.title}\0{passage.text}\0".encode()
            )
        return digest.hexdigest()

    def _build_index(self) -> pt.terrier.TerrierIndex:
        fingerprint_path = self._index_dir / "passages.sha256"
        fingerprint = self._fingerprint()

        with _TERRIER_LOCK:
            index = pt.terrier.TerrierIndex(str(self._index_dir))

            if (
                fingerprint_path.is_file()
                and fingerprint_path.read_text().strip() == fingerprint
            ):
                print(f"[{self._corpus_name}] reusing cached index")
                return index

            if self._index_dir.exists():
                shutil.rmtree(self._index_dir)

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
            fingerprint_path.write_text(fingerprint)

        return index


class CorpusIndex:
    def __init__(self, retrievers: dict[str, CorpusRetriever]) -> None:
        self._retrievers = retrievers

    @property
    def corpora(self) -> list[str]:
        return list(self._retrievers)

    @classmethod
    async def build(cls, corpora: dict[str, PreparedCorpus]) -> CorpusIndex:
        print("Building corpus indexes...")
        start = time.perf_counter()
        loop = asyncio.get_running_loop()

        def _build_retriever(name: str, corpus: PreparedCorpus) -> CorpusRetriever:
            return CorpusRetriever(name, corpus.passages, corpus.language)

        tasks = [
            loop.run_in_executor(None, _build_retriever, name, corpus)
            for name, corpus in corpora.items()
            if corpus.passages
        ]
        retrievers = await asyncio.gather(*tasks)

        print(f"Corpus indexes built in {time.perf_counter() - start:.2f}s")
        return cls(dict(zip(corpora.keys(), retrievers)))

    async def search(
        self,
        queries: list[str],
        depth: int = RETRIEVAL_DEPTH,
        wmodel: str = RETRIEVAL_WMODEL,
        corpora: list[str] | None = None,
    ) -> list[FusedHit]:
        """Run every query against every corpus and fuse the ranked lists."""
        _validate_num_results(depth)

        queries = [_validate_query(query) for query in queries]

        targets = corpora if corpora else self.corpora
        retrievers = [
            self._retrievers[name] for name in targets if name in self._retrievers
        ]

        if not retrievers or not queries:
            return []

        loop = asyncio.get_running_loop()
        tasks = [
            loop.run_in_executor(
                None,
                partial(retriever.search, query, num_results=depth, wmodel=wmodel),
            )
            for retriever in retrievers
            for query in queries
        ]
        ranked_lists = await asyncio.gather(*tasks)

        return fuse_by_reciprocal_rank(ranked_lists)


def load_corpora(corpora_root: Path) -> dict[str, Path]:
    if not corpora_root.is_dir():
        raise ValueError(f"Corpora directory does not exist in {corpora_root}")

    corpora = {
        documents_path.parent.name: documents_path
        for documents_path in sorted(corpora_root.glob("*/documents.jsonl.gz"))
    }

    if not corpora:
        raise ValueError(f"No corpora found in {corpora_root}")

    return corpora


def read_documents(documents_path: Path) -> list[Document]:
    documents: list[Document] = []

    with gzip.open(documents_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()

            if not line:
                continue

            documents.append(json.loads(line))

    if not documents:
        raise ValueError(f"No documents found in {documents_path}.")

    return documents


def infer_language(
    corpus_name: str,
    sample_document: Document,
) -> str:
    if corpus_name.endswith("-de"):
        return "de"

    if corpus_name.endswith("-en"):
        return "en"

    language = str(sample_document.get("language", "")).strip().casefold()

    if language in LANGUAGE_CONFIG:
        return language

    raise ValueError(
        f"Cannot infer a supported language for corpus {corpus_name!r}; "
        "expected a '-de'/'-en' folder suffix or a 'language' document field."
    )


def _load_and_prepare_corpus(
    corpus_name: str,
    documents_path: Path,
) -> tuple[str, PreparedCorpus]:
    documents = read_documents(documents_path)
    n_original = len(documents)
    documents = deduplicate_documents(documents)
    print(
        f"[{corpus_name}] removed {n_original - len(documents)} empty/duplicate documents"
    )

    if not documents:
        raise ValueError(
            f"Corpus {corpus_name!r} has no documents after deduplication."
        )

    language = infer_language(corpus_name, documents[0])

    passages = {
        passage.passage_id: passage
        for doc in documents
        for passage in split_into_passages(
            corpus_name, doc["doc_id"], doc["title"], doc["content"], language
        )
    }
    return corpus_name, PreparedCorpus(passages, language)


async def load_and_prepare_corpora(
    corpora_root: Path,
    *,
    max_workers: int | None = None,
) -> dict[str, PreparedCorpus]:
    print(f"Preparing corpora from {corpora_root}...")

    start = time.perf_counter()
    loop = asyncio.get_running_loop()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        tasks = [
            loop.run_in_executor(executor, _load_and_prepare_corpus, name, path)
            for name, path in load_corpora(corpora_root).items()
        ]
        results = await asyncio.gather(*tasks)

    print(f"Corpora prepared in {time.perf_counter() - start:.2f}s")
    return dict(results)


async def build_index(
    corpora_root: Path, *, max_workers: int | None = None
) -> CorpusIndex:
    prepared_corpora = await load_and_prepare_corpora(
        corpora_root,
        max_workers=max_workers,
    )
    return await CorpusIndex.build(prepared_corpora)
