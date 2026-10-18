from __future__ import annotations

import asyncio
import time
from pathlib import Path

from src.config import (
    RETRIEVAL_DEPTH,
    RETRIEVAL_WMODEL,
)

from .corpora import PreparedCorpus, prepare_corpora
from .dense import DenseIndex
from .fusion import FusedHit, fuse_by_reciprocal_rank
from .lexical import LexicalIndex
from .passages import Passage


async def build_index(
    corpora_root: Path, *, max_workers: int | None = None
) -> CorpusIndex:
    prepared_corpora = await prepare_corpora(corpora_root, max_workers=max_workers)
    return await CorpusIndex.build(prepared_corpora)


class Index:
    def __init__(self, lexical: LexicalIndex, dense: DenseIndex | None = None) -> None:
        self._lexical = lexical
        self._dense = dense

    @property
    def corpora(self) -> list[str]:
        return list(self._lexical.retrievers)


class CorpusIndex:
    def __init__(self, lexical: LexicalIndex, dense: DenseIndex) -> None:
        self._lexical = lexical
        self._dense = dense

    @property
    def corpora(self) -> list[str]:
        return list(self._lexical.retrievers)

    def language(self, corpus: str) -> str:
        return self._lexical.retrievers[corpus].language

    def previous_passage(self, passage: Passage) -> Passage | None:
        """Previous indexed passage of the same document, for scope continuity."""
        if passage.index < 1:
            return None
        retriever = self._lexical.retrievers.get(passage.corpus)
        if retriever is None:
            return None
        return retriever._passages.get(f"{passage.doc_id}#{passage.index - 1}")

    @classmethod
    async def build(cls, corpora: dict[str, PreparedCorpus]) -> CorpusIndex:
        print("Building corpus indexes...")
        start = time.perf_counter()

        names = [name for name, corpus in corpora.items() if corpus.passages]

        lexical, dense = await asyncio.gather(
            LexicalIndex.build(corpora, names),
            DenseIndex.build(corpora, names),
        )

        print(f"Corpus indexes built in {time.perf_counter() - start:.2f}s")
        return cls(lexical, dense)

    async def search(
        self,
        queries: dict[str, list[str]],
        questions: dict[str, list[str]],
        depth: int = RETRIEVAL_DEPTH,
        wmodel: str = RETRIEVAL_WMODEL,
    ) -> list[FusedHit]:
        jobs = [asyncio.to_thread(self._lexical.search, queries, depth, wmodel)]
        jobs.append(asyncio.to_thread(self._dense.search, questions, depth))

        results = await asyncio.gather(*jobs)
        ranked_lists = [ranked for group in results for ranked in group]

        return fuse_by_reciprocal_rank(ranked_lists)
