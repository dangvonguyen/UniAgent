"""Conservative evidence checks for the private-purchase reimbursement rule.

The task topic establishes a claim to reimburse a private advance, but it does
not establish eligibility. A missing attachment or an unidentified payer cannot
by itself establish the opposite of a fact. Keep such cases unresolved instead
of using them to reject the application or declare the rule out of scope.
"""

import re

from .models import RuleVerdict


_TOPIC = re.compile(r"reimbursement of privately advanced costs", re.I)
_ABSENCE = re.compile(
    r"\b(?:missing|absent|lack(?:s|ing)?|without|not (?:provided|submitted|attached|"
    r"documented|shown|included)|no (?:evidence|proof|indication|form|documentation)|"
    r"(?:does|do) not (?:provide|show|establish)|fehlt|fehlend|kein(?:e|en|er|es)?|"
    r"nicht (?:belegt|vorgelegt|nachgewiesen))\b",
    re.I,
)
_FORM = re.compile(r"\b(?:form|forms|formular\w*|antrag\w*)\b", re.I)
_TIME = re.compile(r"\b(?:urgen\w*|time.sensitiv\w*|time.pressure|"
                   r"dring\w*|eil\w*|zeitlich)\b", re.I)
_EXPLICIT_CONTRADICTION = re.compile(
    r"\b(?:not urgent|non.urgent|not time.sensitive|kein(?:e|en|er|es)?\s+"
    r"(?:eile|zeitdruck|dringlichkeit)|nicht dring\w*|"
    r"lange im voraus geplant)\b", re.I,
)
_NEGATIVE_URGENCY = re.compile(
    r"\b(?:not|non[ -]?|never)\s*(?:urgent|time[ -]?sensitive)|"
    r"\b(?:no|without)\s+(?:urgency|time pressure)|"
    r"\b(?:nicht|kein(?:e|en|er|es)?)\s+(?:dring\w*|zeitdruck|eile)", re.I,
)
_SMALLNESS_CLAIM = re.compile(
    r"\b(?:not\s+(?:a\s+)?small|too\s+(?:large|expensive)|"
    r"exceed\w*\s+(?:the\s+)?small|above\s+(?:the\s+)?small|"
    r"small[ \-‑–]?purchase\s+(?:exception|limit|threshold)|"
    r"keine?\s+klein\w*|zu\s+(?:groß|teuer))\b", re.I,
)
_EURO_AMOUNT = re.compile(r"(?:€\s*\d[\d.,]*|\d[\d.,]*\s*(?:€|eur\b|euros?\b))", re.I)


def _policy_cutoff_cited(verdict: RuleVerdict) -> bool:
    """The same numeric amount must be explicitly in the reason and policy.

    A cost on the invoice alone cannot invent a definition for ``kleinere``.
    """
    def amount(item: str) -> str:
        return re.search(r"\d[\d.,]*", item).group(0).replace(",", ".")

    reason_amounts = {amount(item) for item in _EURO_AMOUNT.findall(verdict.reason)}
    policy_amounts = {
        amount(item)
        for quote in verdict.policy_quotes for item in _EURO_AMOUNT.findall(quote.quote)
    }
    return bool(reason_amounts & policy_amounts)


def _unresolved(verdict: RuleVerdict, explanation: str, issue: str):
    return verdict.model_copy(update={
        "verdict": "unknown",
        "reason": f"{explanation} [Model proposed fail: {verdict.reason}]",
    }), issue


def guard_private_purchase(
    verdict: RuleVerdict, topic: str
) -> tuple[RuleVerdict, str | None]:
    """Keep unsupported negative verdicts unresolved without asserting compliance.

    This gate applies only to private-purchase eligibility in reimbursement
    cases. It does not decide which route or product category is permitted.
    The reason classifier guards the observed absence-only failure modes; it
    cannot verify every semantic claim by the model.
    """
    if verdict.rule_id != "private_purchase_eligibility" or not _TOPIC.search(topic):
        return verdict, None

    if verdict.verdict == "not_applicable":
        return verdict.model_copy(update={
            "verdict": "unknown",
            "reason": ("Private-advance reimbursement is the case topic; "
                       "the rule's absence has not been established by the case. "
                       f"[Model proposed not_applicable: {verdict.reason}]"),
        }), "unsupported_not_applicable"

    if verdict.verdict != "fail":
        return verdict, None

    reason = verdict.reason
    quotes = [q.quote for q in verdict.case_quotes]
    if _NEGATIVE_URGENCY.search(reason) and not any(
        _EXPLICIT_CONTRADICTION.search(q) for q in quotes
    ):
        return _unresolved(
            verdict,
            "Non-urgency was asserted without a cited document explicitly showing it; "
            "a price or missing urgency note cannot establish this negative fact.",
            "unsupported_non_urgency_assertion",
        )
    if _SMALLNESS_CLAIM.search(reason) and not _policy_cutoff_cited(verdict):
        return _unresolved(
            verdict,
            "The cited policy does not supply the numerical cutoff asserted for a small purchase.",
            "unsupported_smallness_threshold",
        )
    if not _ABSENCE.search(reason):
        return verdict, None

    if _FORM.search(reason):
        if any(_FORM.search(q) and _ABSENCE.search(q) for q in quotes):
            return verdict, None  # The submitted document explicitly says the form is absent.
        return verdict.model_copy(update={
            "verdict": "unknown",
            "reason": ("A reimbursement form cannot be shown absent merely because "
                       "the submitted evidence packet contains receipts only. "
                       f"[Model proposed fail: {reason}]"),
        }), "form_absence_inferred_from_packet"

    if _TIME.search(reason) and not any(_EXPLICIT_CONTRADICTION.search(q) for q in quotes):
        return verdict.model_copy(update={
            "verdict": "unknown",
            "reason": ("The case does not document whether the purchase was urgent; "
                       "lack of an urgency statement does not prove that it was not urgent. "
                       f"[Model proposed fail: {reason}]"),
        }), "urgency_absence_inferred_from_packet"

    return verdict, None
