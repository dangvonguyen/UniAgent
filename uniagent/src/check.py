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
    "source of the rule. Determine which administrative action these documents "
    "request and what stage the application is in. Before deciding a violation, "
    "identify the condition that triggers the requirement and the event by which "
    "compliance is due. A pending request before a future deadline is not itself "
    "proof of violating that deadline. Do not require evidence of a later approval, "
    "purchase, trip, or reimbursement claim during an earlier application stage, "
    "unless the cited policy expressly requires it now. Do require evidence that "
    "the policy mandates at this submission stage. Distinguish a documented cost "
    "from a no-receipt allowance and a requested estimate from an actual claim. "
    "Verdicts: pass (applicable and satisfied), fail (applicable and already due "
    "but violated, supported by verbatim case quotes), not_applicable (not "
    "triggered or not yet due at this stage), unknown (genuinely cannot decide)."
)


class CheckQuote(BaseModel):
    doc: str
    quote: str


class CheckAnswer(BaseModel):
    verdict: Verdict = "unknown"
    reason: str = ""
    case_quotes: list[CheckQuote] = []
    policy_refs: list[str] = []


def finalize_answer(case: Case, resolved: ResolvedRule,
                    answer: CheckAnswer) -> tuple[RuleVerdict, list[dict[str, str]]]:
    """Deterministic citation validation; also used by offline replay."""
    documents = {f"C{i}": doc for i, doc in enumerate(case.documents, 1)}
    policy = {f"E{i}": quote for i, quote in enumerate(resolved.quotes, 1)}
    issues: list[dict[str, str]] = []
    case_quotes = []
    for item in answer.case_quotes:
        document = documents.get(item.doc)
        if document is None:
            issues.append({"kind": "invalid_case_document", "source": item.doc})
        elif not verified(item.quote, document.text):
            issues.append({"kind": "case_quote_not_found", "source": item.doc})
        else:
            case_quotes.append(CaseQuote(document=document.name, quote=item.quote))
    policy_quotes = []
    for ref in answer.policy_refs:
        if ref in policy:
            policy_quotes.append(policy[ref])
        else:
            issues.append({"kind": "invalid_policy_reference", "source": ref})
    verdict = answer.verdict
    reason = answer.reason
    if verdict == "fail" and not case_quotes:
        issues.append({"kind": "fail_without_verified_case_quote", "source": ""})
        verdict = "unknown"
        reason += " [Model proposed fail; no case excerpt passed source validation.]"
    return RuleVerdict(rule_id=resolved.rule.id, verdict=verdict, reason=reason,
                       case_quotes=case_quotes, policy_quotes=policy_quotes), issues


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
        trace.log("citation_audit", output={"rule_id": rule.id,
                    "model_verdict": None, "final_verdict": "unknown",
                    "issues": [{"kind": "no_policy_quote", "source": ""}]})
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
            SYSTEM, user, CheckAnswer, context=f"{case.case_id}:check_rule:{rule.id}"
        )
    except Exception as error:  # noqa: BLE001
        trace.log("error", status="error", error=str(error))
        trace.log("citation_audit", output={"rule_id": rule.id,
                    "model_verdict": None, "final_verdict": "unknown",
                    "issues": [{"kind": "model_error", "source": str(error)[:150]}]})
        return RuleVerdict(
            rule_id=rule.id, verdict="unknown", reason=f"LLM error: {error}"
        )

    verdict, issues = finalize_answer(case, resolved, answer)
    trace.log("citation_audit", output={"rule_id": rule.id,
                "model_verdict": answer.verdict, "final_verdict": verdict.verdict,
                "issues": issues})
    return verdict
