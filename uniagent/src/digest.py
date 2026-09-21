"""Resolve each rule against the corpora once per run."""

import asyncio

from pydantic import BaseModel

from .config import DIGEST_MAX_DOC_CHARS, DIGEST_TOP_K
from .llm import LLM, verified
from .models import PolicyQuote, ResolvedRule, Rule
from .retrieval import CorpusIndex, SearchHit
from .tracelog import Trace

SYSTEM = (
    "You review a university's regulations. You receive a rule to look up and numbered "
    "document excerpts (D1, D2, ...). Return only verbatim quotes from the excerpts that "
    "state the rule itself, in full: with all conditions, amounts, deadlines and "
    "exceptions. Copy quotes exactly in their original language; never translate or "
    "invent. If no excerpt states the rule, return an empty list."
)


class ExtractItem(BaseModel):
    doc: str
    quote: str


class ExtractAnswer(BaseModel):
    items: list[ExtractItem] = []


async def build_digest(
    rules: list[Rule], index: CorpusIndex, llm: LLM, trace: Trace
) -> list[ResolvedRule]:
    """Resolve every rule against the mounted corpora once per run."""

    async def _run_task(rule: Rule) -> list[PolicyQuote]:
        with trace.case(f"rule:{rule.id}"):
            return await _resolve_rule(rule, index, llm, trace)

    tasks = [_run_task(rule) for rule in rules]
    quotes = await asyncio.gather(*tasks)
    return [
        ResolvedRule(rule=rule, quotes=rule_quotes)
        for rule, rule_quotes in zip(rules, quotes, strict=True)
    ]


async def _resolve_rule(
    rule: Rule, index: CorpusIndex, llm: LLM, trace: Trace
) -> list[PolicyQuote]:
    trace.log(
        "input",
        input={"rule_id": rule.id, "check": rule.check, "queries": rule.queries},
    )

    hits: dict[tuple[str, str], SearchHit] = {}
    for query in rule.queries:
        trace.log(
            "tool_call",
            tool="corpus_search",
            input={"query": query, "num_results": DIGEST_TOP_K},
        )
        results = index.search(query, num_results=DIGEST_TOP_K)
        trace.log(
            "observation",
            output={
                "hits": [
                    {
                        "corpus": hit.passage.corpus,
                        "passage_id": hit.passage.passage_id,
                        "score": hit.score,
                    }
                    for hit in results
                ]
            },
        )
        for hit in results:
            key = (hit.passage.corpus, hit.passage.passage_id)
            if key not in hits or hit.score > hits[key].score:
                hits[key] = hit
    top = sorted(hits.values(), key=lambda hit: hit.score, reverse=True)[:DIGEST_TOP_K]
    docs = {f"D{i}": hit for i, hit in enumerate(top, 1)}
    if not docs:
        return []

    excerpts = {
        label: hit.excerpt[:DIGEST_MAX_DOC_CHARS] for label, hit in docs.items()
    }

    user = _build_user_message(rule, excerpts)

    try:
        answer = await llm.complete_json(
            SYSTEM, user, ExtractAnswer, context=f"resolve_rule:{rule.id}"
        )
    except Exception as error:  # noqa: BLE001
        trace.log("error", status="error", error=str(error))
        return []

    return [
        PolicyQuote(
            corpus=docs[item.doc].passage.corpus,
            doc_id=docs[item.doc].passage.doc_id,
            quote=item.quote,
        )
        for item in answer.items
        if item.doc in excerpts and verified(item.quote, excerpts[item.doc])
    ]


def _build_user_message(rule, excerpts) -> str:
    user = f"Rule: {rule.check}\n\n" + "\n\n".join(
        f"[{label}]\n{text}" for label, text in excerpts.items()
    )
    return user
