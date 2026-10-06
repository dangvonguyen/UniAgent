import hashlib
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import asdict
from pathlib import Path

from src.config import DIGEST_CONTEXT_K, DIGEST_MAX_DOC_CHARS
from src.models import Rule
from src.retrieval import FusedHit
from src.retrieval.corpora import PreparedCorpus, read_documents
from src.text import normalize_text

from .gold import Gold, GoldQuote
from .metrics import QuoteResult, locate_quote, squash

SearchFn = Callable[[Rule], Awaitable[list[FusedHit]]]
RECALL_DEPTHS = (50, 100)


def equivalent_doc_ids(
    corpora_paths: dict[str, Path], gold: Gold
) -> dict[tuple[str, str], frozenset[str]]:
    """Every doc_id whose body is identical to a gold document's (duplicates in the crawl)."""
    wanted: dict[str, set[str]] = defaultdict(set)
    for quotes in gold.values():
        for quote in quotes:
            wanted[quote.corpus].add(quote.doc_id)

    result: dict[tuple[str, str], frozenset[str]] = {}
    for corpus, doc_ids in wanted.items():
        by_hash: dict[str, set[str]] = defaultdict(set)
        gold_hash: dict[str, str] = {}
        for doc in read_documents(corpora_paths[corpus]):
            content = doc.get("content", "")
            if not isinstance(content, str) or not content.strip():
                continue
            digest = hashlib.sha256(normalize_text(content).encode("utf-8")).hexdigest()
            by_hash[digest].add(doc["doc_id"])
            if doc["doc_id"] in doc_ids:
                gold_hash[doc["doc_id"]] = digest
        for doc_id in doc_ids:
            result[(corpus, doc_id)] = frozenset(
                by_hash.get(gold_hash.get(doc_id, ""), {doc_id})
            )
    return result


def count_whole_passages(
    prepared: dict[str, PreparedCorpus], quote: GoldQuote, doc_ids: frozenset[str]
) -> int:
    """Passages that hold the whole quote untruncated. 0 means the splitter cut it apart."""
    needle = squash(quote.quote)
    passages = prepared[quote.corpus].passages.values()
    return sum(
        1
        for passage in passages
        if passage.doc_id in doc_ids and needle in squash(passage.text)
    )


async def evaluate_coverage(
    rules: list[Rule],
    gold: Gold,
    search: SearchFn,
    prepared: dict[str, PreparedCorpus],
    equivalents: dict[tuple[str, str], frozenset[str]],
    *,
    k: int = DIGEST_CONTEXT_K,
    max_chars: int = DIGEST_MAX_DOC_CHARS,
) -> dict:
    rule_reports = []
    all_results: list[QuoteResult] = []

    for rule in rules:
        quotes = gold.get(rule.id, [])
        if not quotes:
            rule_reports.append({"rule_id": rule.id, "status": "no_gold"})
            continue

        hits = await search(rule)
        results = []
        for quote in quotes:
            doc_ids = equivalents[(quote.corpus, quote.doc_id)]
            results.append(
                locate_quote(
                    quote,
                    hits,
                    equivalent_doc_ids=doc_ids,
                    max_chars=max_chars,
                    whole_passages=count_whole_passages(prepared, quote, doc_ids),
                )
            )
        all_results.extend(results)

        rule_reports.append(
            {
                "rule_id": rule.id,
                "status": "measured",
                "candidates": len(hits),
                f"coverage@{k}": _share(results, k),
                **{f"recall@{d}": _share(results, d) for d in RECALL_DEPTHS},
                "all_required_in_top_k": all(r.within(k) for r in results),
                "quotes": [asdict(result) for result in results],
            }
        )

    measured = [r for r in rule_reports if r["status"] == "measured"]
    return {
        "k": k,
        "max_chars": max_chars,
        "rules": rule_reports,
        "summary": {
            "rules_measured": len(measured),
            "rules_without_gold": [
                r["rule_id"] for r in rule_reports if r["status"] == "no_gold"
            ],
            "rules_meeting_bar": sum(r["all_required_in_top_k"] for r in measured),
            f"coverage@{k}": _share(all_results, k),
            **{f"recall@{d}": _share(all_results, d) for d in RECALL_DEPTHS},
            "quotes_split_by_passages": [
                r.key for r in all_results if r.whole_passages == 0
            ],
        },
    }


def _share(results: list[QuoteResult], k: int) -> float:
    return sum(r.within(k) for r in results) / len(results) if results else 0.0
