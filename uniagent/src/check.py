import asyncio
import subprocess
from pathlib import Path

from pydantic import BaseModel

from .llm import LLM, verified
from .models import Case, CaseDocument, CaseQuote, ResolvedRule, RuleVerdict, Verdict
from .tracelog import Trace

SYSTEM = (
    "You review university business trip applications. You receive a rule, the policy "
    "quotes that define it (E1, E2, ...) and the case documents (C1, C2, ...). Apply the "
    "rule exactly as the quoted policy states it, including all exceptions and "
    "justification conditions. Case documents only establish facts; they are never a "
    "source of the rule. Verdicts: pass (rule satisfied), fail (rule violated, supported "
    "by verbatim quotes from the case documents in their original language), "
    "not_applicable (rule does not concern this case), unknown (cannot be decided)."
)


class CheckQuote(BaseModel):
    doc: str
    quote: str


class CheckAnswer(BaseModel):
    verdict: Verdict = "unknown"
    reason: str = ""
    case_quotes: list[CheckQuote] = []
    policy_refs: list[str] = []


def load_case(case_dir: Path) -> Case:
    return Case(
        case_id=case_dir.name,
        documents=[
            CaseDocument(
                name=pdf.name,
                text=subprocess.run(
                    ["pdftotext", "-layout", str(pdf), "-"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout,
            )
            for pdf in sorted(case_dir.glob("*.pdf"))
        ],
    )


async def check_case(
    case: Case, rules: list[ResolvedRule], llm: LLM, trace: Trace
) -> list[RuleVerdict]:
    tasks = [_check_rule(case, resolved, llm, trace) for resolved in rules]
    return list(await asyncio.gather(*tasks))


async def _check_rule(
    case: Case, resolved: ResolvedRule, llm: LLM, trace: Trace
) -> RuleVerdict:
    rule = resolved.rule
    policy = {f"E{i}": q for i, q in enumerate(resolved.quotes, 1)}
    trace.log(
        "observation",
        output={
            "rule_id": rule.id,
            "policy_quotes": [
                {"corpus": q.corpus, "doc_id": q.doc_id, "quote": q.quote}
                for q in resolved.quotes
            ],
        },
    )
    if not policy:
        return RuleVerdict(
            rule_id=rule.id, verdict="unknown", reason="No policy found in the corpus."
        )

    documents = {f"C{i}": doc for i, doc in enumerate(case.documents, 1)}
    user = (
        f"Rule: {rule.check}\n\nPolicy quotes:\n"
        + "\n".join(f"[{label}] ({e.doc_id}) {e.quote}" for label, e in policy.items())
        + "\n\nCase documents:\n\n"
        + "\n\n".join(f"[{label}] {d.name}\n{d.text}" for label, d in documents.items())
    )
    try:
        answer = await llm.complete_json(
            SYSTEM, user, CheckAnswer, context=f"check_rule:{rule.id}"
        )
    except Exception as error:  # noqa: BLE001
        trace.log("error", status="error", error=str(error))
        return RuleVerdict(
            rule_id=rule.id, verdict="unknown", reason=f"LLM error: {error}"
        )

    case_quotes = [
        CaseQuote(document=documents[q.doc].name, quote=q.quote)
        for q in answer.case_quotes
        if q.doc in documents and verified(q.quote, documents[q.doc].text)
    ]
    verdict = answer.verdict
    if verdict == "fail" and not case_quotes:
        verdict = "unknown"
    return RuleVerdict(
        rule_id=rule.id,
        verdict=verdict,
        reason=answer.reason,
        case_quotes=case_quotes,
        policy_quotes=[policy[ref] for ref in answer.policy_refs if ref in policy],
    )
