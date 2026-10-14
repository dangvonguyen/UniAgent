from __future__ import annotations

import asyncio
import time
from pathlib import Path

from src.config import (
    GTE_MAX_LENGTH,
    RETRIEVAL_DEPTH,
    RETRIEVAL_GTE_WEIGHT,
    RETRIEVAL_RRF_K,
    RETRIEVAL_SPARSE_WEIGHT,
    RETRIEVAL_WMODEL,
)

from .corpora import PreparedCorpus, prepare_corpora
from .fusion import (
    FusedHit,
    fuse_by_reciprocal_rank,
    weighted_fuse_by_reciprocal_rank,
)
from .lexical import LexicalIndex
from .rerank import GteReranker, load_gte_model


async def build_index(
    corpora_root: Path, *, max_workers: int | None = None
) -> CorpusIndex:
    prepared_corpora = await prepare_corpora(corpora_root, max_workers=max_workers)
    return await CorpusIndex.build(prepared_corpora)


class CorpusIndex:
    def __init__(self, lexical: LexicalIndex, reranker: GteReranker) -> None:
        self._lexical = lexical
        self._reranker = reranker

    @property
    def corpora(self) -> list[str]:
        return list(self._lexical.retrievers)

    def language(self, corpus: str) -> str:
        return self._lexical.retrievers[corpus].language

    @classmethod
    async def build(cls, corpora: dict[str, PreparedCorpus]) -> CorpusIndex:
        print("Building corpus indexes...")
        start = time.perf_counter()

        names = [name for name, corpus in corpora.items() if corpus.passages]

        lexical, gte_model = await asyncio.gather(
            LexicalIndex.build(corpora, names),
            asyncio.to_thread(load_gte_model, GTE_MAX_LENGTH),
        )

        print(f"Corpus indexes built in {time.perf_counter() - start:.2f}s")
        return cls(lexical, GteReranker(gte_model))

    async def search(
        self,
        queries: dict[str, list[str]],
        questions: dict[str, list[str]],
        depth: int = RETRIEVAL_DEPTH,
        wmodel: str = RETRIEVAL_WMODEL,
    ) -> list[FusedHit]:
        sparse_lists = await asyncio.to_thread(
            self._lexical.search, queries, depth, wmodel
        )
        sparse_hits = fuse_by_reciprocal_rank(sparse_lists)
        gte_hits = await asyncio.to_thread(
            self._reranker.rerank, sparse_hits, questions, self.language
        )
        return weighted_fuse_by_reciprocal_rank(
            (
                (sparse_hits, RETRIEVAL_SPARSE_WEIGHT),
                (gte_hits, RETRIEVAL_GTE_WEIGHT),
            ),
            rrf_k=RETRIEVAL_RRF_K,
        )
