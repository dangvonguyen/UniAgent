from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from src.config import RETRIEVAL_RRF_K

from .passages import Passage


@dataclass(frozen=True)
class SearchHit:
    """One result of a single query against a single corpus."""

    passage: Passage
    score: float


@dataclass(frozen=True)
class FusedHit:
    """One result of the fused ranking; `score` is its reciprocal-rank-fusion score."""

    passage: Passage
    score: float

    @property
    def excerpt(self) -> str:
        return f"{self.passage.title}\n\n{self.passage.text}"


def fuse_by_reciprocal_rank(
    ranked_lists: Iterable[list[SearchHit]], *, rrf_k: int = RETRIEVAL_RRF_K
) -> list[FusedHit]:
    """Merge ranked result lists into one ranking, best first."""
    return weighted_fuse_by_reciprocal_rank(
        ((hits, 1.0) for hits in ranked_lists), rrf_k=rrf_k
    )


def weighted_fuse_by_reciprocal_rank(
    ranked_lists: Iterable[tuple[Sequence[SearchHit | FusedHit], float]],
    *,
    rrf_k: int = RETRIEVAL_RRF_K,
) -> list[FusedHit]:
    """Merge rankings with weighted RRF, retaining the union of candidates."""
    if rrf_k < 1:
        raise ValueError("rrf_k must be positive")

    scores: dict[tuple[str, str], float] = defaultdict(float)
    passages: dict[tuple[str, str], Passage] = {}

    for hits, weight in ranked_lists:
        if weight < 0:
            raise ValueError("RRF weights must be nonnegative")
        for rank, hit in enumerate(hits, 1):
            key = (hit.passage.corpus, hit.passage.passage_id)
            scores[key] += weight / (rrf_k + rank)
            passages.setdefault(key, hit.passage)

    return [
        FusedHit(passage=passages[key], score=scores[key])
        for key in sorted(scores, key=lambda key: (-scores[key], key))
    ]
