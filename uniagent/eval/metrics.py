import math
import re
from collections.abc import Collection, Sequence
from dataclasses import dataclass

from src.retrieval import FusedHit
from src.retrieval.passages import normalize_text

from .gold import GoldQuote


def squash(text: str) -> str:
    """Whitespace-insensitive form, so line wrapping cannot break a verbatim match."""
    return re.sub(r"\s+", " ", normalize_text(text)).strip()


@dataclass(frozen=True)
class QuoteResult:
    key: str
    passage_rank: int | None  # first fused hit whose visible excerpt holds the quote
    doc_rank: int | None  # first fused hit from the quote's document (or a copy of it)
    whole_passages: (
        int  # passages holding the whole quote untruncated (0 = split or absent)
    )

    def within(self, k: int) -> bool:
        return self.passage_rank is not None and self.passage_rank <= k


def locate_quote(
    quote: GoldQuote,
    hits: Sequence[FusedHit],
    *,
    equivalent_doc_ids: Collection[str],
    max_chars: int,
    whole_passages: int,
) -> QuoteResult:
    """Rank of the quote in `hits`, judged on the excerpt as truncated for the LLM."""
    needle = squash(quote.quote)
    passage_rank = doc_rank = None

    for rank, hit in enumerate(hits, 1):
        passage = hit.passage
        if passage.corpus != quote.corpus:
            continue
        if doc_rank is None and passage.doc_id in equivalent_doc_ids:
            doc_rank = rank
        if passage_rank is None and needle in squash(hit.excerpt[:max_chars]):
            passage_rank = rank
        if passage_rank is not None and doc_rank is not None:
            break

    return QuoteResult(quote.key, passage_rank, doc_rank, whole_passages)


def ndcg_at_k(
    ranked_ids: Sequence[str], relevant: Collection[str], k: int = 10
) -> float:
    """Binary-relevance nDCG@k; 0.0 when nothing is judged relevant."""
    if not relevant:
        return 0.0
    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, doc_id in enumerate(ranked_ids[:k], 1)
        if doc_id in relevant
    )
    ideal = sum(
        1.0 / math.log2(rank + 1) for rank in range(1, min(len(relevant), k) + 1)
    )
    return dcg / ideal


def unique_in_order(ids: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(ids))
