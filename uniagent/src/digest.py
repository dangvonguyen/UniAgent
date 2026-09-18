"""Resolve each rule against the corpora once per run."""

from pydantic import BaseModel

from .llm import LLM, verified
from .models import PolicyQuote, ResolvedRule, Rule
from .retrieval import CorpusIndex

TOP_K = 3
MAX_DOC_CHARS = 3000

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


def build_digest(rules: list[Rule], index: CorpusIndex, llm: LLM) -> list[ResolvedRule]:
    """Resolve every rule against the mounted corpora once per run."""
    return [ResolvedRule(rule=rule, quotes=_resolve_rule(rule, index, llm)) for rule in rules]


def _resolve_rule(rule: Rule, index: CorpusIndex, llm: LLM) -> list[PolicyQuote]:
    hits: dict[tuple[str, str], dict] = {}
    for query in rule.queries:
        for hit in index.search(query, num_results=TOP_K):
            key = (hit["corpus"], hit["docno"])
            if key not in hits or hit["score"] > hits[key]["score"]:
                hits[key] = hit
    top = sorted(hits.values(), key=lambda hit: hit["score"], reverse=True)[:TOP_K]
    docs = {f"D{i}": hit for i, hit in enumerate(top, 1)}
    if not docs:
        return []

    excerpts = {label: hit["text"][:MAX_DOC_CHARS] for label, hit in docs.items()}

    user = _build_user_message(rule, excerpts)

    try:
        answer = llm.complete_json(SYSTEM, user, ExtractAnswer)
    except Exception:  # noqa: BLE001
        return []

    return [
        PolicyQuote(
            corpus=docs[item.doc]["corpus"],
            doc_id=docs[item.doc]["docno"],
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
