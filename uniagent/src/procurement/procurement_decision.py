"""Turn deterministic procurement PDF findings into verdicts, conservatively.

An audit finding is a *diagnostic*. It becomes a business `fail` only when
  (A) its kind is in SELF_CONTRADICTION_KINDS -- the submitted PDFs contradict
      each other, which needs no external duty (team decision), or
  (B) the retrieved duty and PDF fields verify the comparison method, the
      offer count, and the stated framework exception. Other policy claims
      remain diagnostics without a scoped semantic review.
Everything else is traced as `audit_diagnostic` and never changes the label.
Other task domains are untouched.
"""

from dataclasses import asdict
import re
from pathlib import Path

from ..models import CaseQuote, PolicyQuote, ResolvedRule, RuleVerdict
from .obligation_gate import obligation_errors
from .procurement_audit import Finding, audit_case, audit_coverage, policy_offer_count_from_quotes
from ..quotes import match_case_quote
from ..tracelog import Trace

# Only two source-backed, material contradictions are enabled. The audit
# extracts the underlying PDF text; it checks numerical materiality before
# emitting these findings. This is an input-integrity decision, not a claim
# that an external procurement policy mandates a particular award.
SELF_CONTRADICTION_KINDS: frozenset[str] = frozenset({
    "form_total", "offer_vs_award_note",
})

# Tier B. Which duty a policy-based finding relies on. Extend a kind here only
# after the source scan shows a scoped obligation for it (see README).
OBLIGATION_FOR_KIND: dict[str, str] = {
    "declared_method_missing_offers": "min_offers",
}


def _split_sources(f: Finding) -> tuple[list[CaseQuote], list[PolicyQuote]]:
    case_quotes, policy_quotes = [], []
    for s in f.sources:
        if s.document.lower().endswith(".pdf"):
            case_quotes.append(CaseQuote(document=s.document, quote=s.quote))
            continue
        corpus, separator, doc_id = s.document.partition("/")
        if separator:
            policy_quotes.append(PolicyQuote(corpus=corpus, doc_id=doc_id, quote=s.quote))
    return case_quotes, policy_quotes


def classify(f: Finding) -> tuple[str, list[str]]:
    """('fail' | 'diagnostic', reasons). Pure; no I/O."""
    if f.basis == "document":  # tier A: the PDFs contradict themselves
        if f.kind in SELF_CONTRADICTION_KINDS:
            return "fail", []
        return "diagnostic", ["self-contradiction-kind-not-enabled"]
    kind = OBLIGATION_FOR_KIND.get(f.kind)  # tier B: needs a verified duty quote
    _, policy_quotes = _split_sources(f)
    if kind is None:
        return "diagnostic", ["no-obligation-kind-for-finding"]
    if not policy_quotes:
        return "diagnostic", ["no-policy-quote-attached"]
    errors = [e for q in policy_quotes for e in obligation_errors(kind, q.quote, q.quote)]
    if errors:
        return "diagnostic", errors
    if f.kind == "declared_method_missing_offers":
        case_quotes, _ = _split_sources(f)
        has_comparison = any(re.search(r"(?i)^\s*Vergabeart\s*(?:\|\s*)?Preisvergleich\b", q.quote)
                             for q in case_quotes)
        has_count = any(re.search(r"(?i)^\s*Eingeholte\s+Angebote\s*(?:\|\s*)?\d+\b", q.quote)
                        for q in case_quotes)
        explicit_no = any(re.search(
            r"(?i)^\s*Rahmenvertragsprodukt\s*(?:\|\s*)?\[\s*\]\s*ja\s+\[\s*[Xx]\s*\]\s*nein\b",
            q.quote,
        ) for q in case_quotes)
        general_duty = any(re.search(
            r"(?i)Grundsätzlich\s+müssen\s+(?:\d+|ein|eins|eine|zwei|drei|vier|fünf|sechs)\s+Angebote\s+eingeholt\s+werden",
            q.quote,
        ) and re.search(r"(?i)Ausnahme\s+bei\s+Rahmenvertrag", q.quote)
            for q in policy_quotes)
        if has_comparison and has_count and explicit_no and general_duty:
            # audit_case already checked the quoted number > declared and
            # counted the attached offers across all submitted PDF texts.
            return "fail", []
        return "diagnostic", ["comparison-method-or-framework-exception-unverified"]
    # The lexical gate alone cannot establish the scope and exceptions of
    # other policy-based findings.
    return "diagnostic", ["obligation-scope-stage-exceptions-not-verified"]


def procurement_audit_verdicts(
    case_dir: Path, resolved: list[ResolvedRule], trace: Trace,
    documents: dict[str, str] | None = None,
) -> list[RuleVerdict]:
    policy_items = [quote.model_dump() for r in resolved for quote in r.quotes]
    policy = policy_offer_count_from_quotes(policy_items)
    count, source = policy if policy else (None, None)
    findings = audit_case(case_dir, count, source, documents)
    case_texts = documents or {}
    known_policies = {(q.corpus, q.doc_id, q.quote)
                      for r in resolved for q in r.quotes}
    result: list[RuleVerdict] = []
    dispositions = []
    for f in findings:
        disposition, reasons = classify(f)
        if documents is not None:
            case_quotes, policy_quotes = _split_sources(f)
            if not case_quotes or any(
                    q.document not in case_texts or
                    match_case_quote(q.quote, case_texts[q.document]) is None
                    for q in case_quotes):
                disposition = "diagnostic"
                reasons.append("audit-case-source-not-verified")
            if any((q.corpus, q.doc_id, q.quote) not in known_policies
                   for q in policy_quotes):
                disposition = "diagnostic"
                reasons.append("audit-policy-source-not-in-digest")
        dispositions.append({**asdict(f), "disposition": disposition, "gate": reasons})
        if disposition != "fail":
            continue
        case_quotes, policy_quotes = _split_sources(f)
        result.append(RuleVerdict(
            rule_id=f.rule_id, verdict="fail", reason=f.detail,
            case_quotes=case_quotes, policy_quotes=policy_quotes,
        ))
    trace.log(
        "observation", tool="procurement_pdf_audit",
        output={
            "policy_offer_count": count,
            "findings": dispositions,
            "coverage_gaps": audit_coverage(case_dir.name, case_texts)
            if documents is not None else {},
            "note": "Enabled PDF contradictions and fully sourced three-offer checks can fail; other findings remain diagnostics.",
        },
    )
    return result
