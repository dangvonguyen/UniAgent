from __future__ import annotations

import asyncio
import hashlib
import shutil
import threading
import time
from functools import partial
from pathlib import Path

import pyterrier as pt

from src.config import (
    INDEX_CACHE_DIR,
    RETRIEVAL_DEPTH,
    RETRIEVAL_DOCNO_META_LENGTH,
    RETRIEVAL_WMODEL,
)

from .corpora import PreparedCorpus, prepare_corpora
from .fusion import FusedHit, SearchHit, fuse_by_reciprocal_rank
from .languages import LANGUAGE_CONFIG
from .passages import Passage

# Terrier's underlying Java state is not thread-safe
_TERRIER_LOCK = threading.Lock()


async def build_index(
    corpora_root: Path, *, max_workers: int | None = None
) -> CorpusIndex:
    prepared_corpora = await prepare_corpora(corpora_root, max_workers=max_workers)
    return await CorpusIndex.build(prepared_corpora)


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

        names = [name for name, corpus in corpora.items() if corpus.passages]
        tasks = [
            loop.run_in_executor(
                None,
                CorpusRetriever,
                name,
                corpora[name].passages,
                corpora[name].language,
            )
            for name in names
        ]
        retrievers = await asyncio.gather(*tasks)

        print(f"Corpus indexes built in {time.perf_counter() - start:.2f}s")
        return cls(dict(zip(names, retrievers, strict=True)))

    async def search(
        self,
        queries: dict[str, list[str]],
        depth: int = RETRIEVAL_DEPTH,
        wmodel: str = RETRIEVAL_WMODEL,
    ) -> list[FusedHit]:
        """Run each query against the corpora in its own language and fuse the ranked lists."""
        pairs = [
            (retriever, query)
            for retriever in self._retrievers.values()
            for query in queries.get(retriever.language, [])
        ]

        if not pairs:
            return []

        loop = asyncio.get_running_loop()
        tasks = [
            loop.run_in_executor(
                None,
                partial(retriever.search, query, depth=depth, wmodel=wmodel),
            )
            for retriever, query in pairs
        ]
        ranked_lists = await asyncio.gather(*tasks)

        return fuse_by_reciprocal_rank(ranked_lists)


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

        self._index_dir = (INDEX_CACHE_DIR / f"index-{corpus_name}").resolve()
        self._index = self._build_index()

    @property
    def language(self) -> str:
        return self._language

    def search(
        self,
        query: str,
        depth: int = RETRIEVAL_DEPTH,
        wmodel: str = RETRIEVAL_WMODEL,
    ) -> list[SearchHit]:
        with _TERRIER_LOCK:
            retriever = self._index.retriever(wmodel, num_results=depth)
            results = retriever.search(query)

        return [
            SearchHit(
                passage=self._passages[row.docno],
                score=float(row.score),
            )
            for row in results.itertuples()
        ]

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

    def _fingerprint(self) -> str:
        """Hash of everything that determines index contents."""
        digest = hashlib.sha256()
        digest.update(f"{self._language}\0{RETRIEVAL_DOCNO_META_LENGTH}\0".encode())
        for passage in self._passages.values():
            digest.update(
                f"{passage.passage_id}\0{passage.title}\0{passage.text}\0".encode()
            )
        return digest.hexdigest()
