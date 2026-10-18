"""Evidence and scope checks for reimbursement rules."""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from ..models import CaseDocument, CaseQuote, PolicyQuote, RuleVerdict


# From reimbursement_reconciliation_scope.py
_INVOICE_ID = re.compile(
    r"(?im)^\s*(?:invoice\s*(?:no\.?|number|#)|"
    r"rechnung\s*(?:nr\.?|nummer)|rechnungsnummer|"
    r"receipt\s*(?:no\.?|number|#)|beleg\s*(?:nr\.?|nummer))"
    r"\s*[:.#-]?\s*([\w-]+)"
)


_CREDIT = re.compile(
    r"(?i)\b(?:gutschrift|credit\s+(?:note|memo)|refund(?:ed)?|"
    r"r[üu]ckerstatt(?:ung|et)|storno(?:rechnung)?)\b"
)


_CLAIMED_TOTAL = re.compile(
    r"(?i)\b(?:zu\s+erstatten|beantragter?\s+(?:betrag|erstattungsbetrag)|"
    r"erstattungsbetrag|claim(?:ed)?\s+(?:amount|total)|"
    r"amount\s+claim(?:ed)?|reimbursement\s+(?:requested|amount))\b"
)


_PAYMENT_RECORD = re.compile(r"(?i)(?:kontoauszug|kreditkartenabrechnung|"
                             r"(?:bank|card|credit.?card)[\s_-]*statement)")


_PAYMENT_HEADER = re.compile(
    r"(?im)^\s*(?:kontoauszug|kreditkartenabrechnung|"
    r"bank\s+statement|credit\s+card\s+statement|card\s+statement)\b"
)


@dataclass(frozen=True)
class Scope:
    active: bool
    reasons: tuple[str, ...]


def inspect_reconciliation_scope(documents: Mapping[str, object]) -> Scope:
    """Activate on multiple bills, an adjustment, or a stated claim amount.

    A single bill plus a bank statement shows one expense and one payment;
    its payer/receipt validity belongs to other reimbursement rules.
    """
    rendered: list[tuple[str, str]] = []
    for item in documents.values():
        name = str(getattr(item, "name", ""))
        body = str(getattr(item, "text", item))
        rendered.append((name, body))
    if not rendered:
        return Scope(False, ("no_expense_document",))

    bodies = "\n".join(body for _, body in rendered)
    reasons: list[str] = []
    if _CREDIT.search(bodies) or any(_CREDIT.search(name) for name, _ in rendered):
        reasons.append("credit_or_refund")
    if _CLAIMED_TOTAL.search(bodies):
        reasons.append("stated_claim_amount")
    invoice_ids = [match.group(1) for match in _INVOICE_ID.finditer(bodies)]
    if len(invoice_ids) >= 2:
        reasons.append("multiple_billing_identifiers")
    else:
        possible_bills = [name for name, body in rendered
                          if not _PAYMENT_RECORD.search(name)
                          and not _PAYMENT_HEADER.search(body[:1200])]
        # An opaque attachment can be another bill. Let the rule inspect it
        # rather than declaring the whole case out of scope from its filename.
        if len(possible_bills) >= 2:
            reasons.append("multiple_possible_billing_documents")

    return Scope(bool(reasons), tuple(reasons) if reasons else ("no_reconciliation_event",))


# From reimbursement_route_scope.py
_ONLINE_EVENT_TOPIC = re.compile(r"reimbursement of privately advanced costs", re.I)


_RECEIPT = re.compile(r"invoice|receipt|rechnung|quittung|beleg", re.I)


_STATEMENT = re.compile(r"kontoauszug|card statement|bank statement|kreditkartenabrechnung", re.I)


_VIRTUAL_ONLY = re.compile(
    r"\b(?:online[ -]?only|only online|exclusively online|fully virtual|"
    r"virtual[ -]?only|ausschlie[ßs]lich online|rein virtuell|"
    r"nur online|vollständig virtuell)\b", re.I
)


_EVENT = re.compile(r"\b(?:workshop|conference|congress|seminar|symposium|"
                    r"konferenz|tagung|kongress|seminar)\b", re.I)


_FEE = re.compile(r"\b(?:participation|registration|attendance|"
                  r"teilnahme(?:gebühr|entgelt)?|anmeldegebühr|"
                  r"registrierungsgebühr)\b", re.I)


_CURRENCY = re.compile(r"(?:\b(?:USD|EUR|GBP)\b|[$€£])\s*\d|\d[\d.,]*\s*(?:USD|EUR|GBP|[$€£])\b", re.I)


_TOTAL = re.compile(r"\b(?:total|gesamt|summe|subtotal|mwst|vat|tax|"
                    r"charged|paid by|bezahlt|zahlung|fee\s+total)\b", re.I)


_IN_PERSON = re.compile(r"\b(?:in.person|onsite|on.site|hybrid|physical attendance|"
                        r"präsenz|vor ort)\b", re.I)


def _charged_lines(text: str) -> list[str]:
    """Potential line items, excluding totals, payment notes and tax lines."""
    return [line.strip() for line in text.splitlines()
            if _CURRENCY.search(line) and not _TOTAL.search(line)]


def online_event_fee_scope(
    documents: Mapping[str, CaseDocument], topic: str
) -> RuleVerdict | None:
    """Return not_applicable only for a clearly fee-only, online-only event.

    Reject mixed receipts and ambiguous virtual/hybrid events so that the SAP
    rule still examines any separately claimed goods. Bank statements are
    payment evidence, not the list of claimed items.
    """
    if not _ONLINE_EVENT_TOPIC.search(topic):
        return None
    receipts = [d for d in documents.values()
                if not _STATEMENT.search(d.name)
                and _RECEIPT.search(d.name + "\n" + d.text)]
    if not receipts:
        return None
    fee_document = None
    fee_line = online_line = None
    for doc in receipts:
        if _IN_PERSON.search(doc.text):
            return None
        lines = _charged_lines(doc.text)
        if not lines or any(not _FEE.search(line) for line in lines):
            return None
        online = next((line.strip() for line in doc.text.splitlines()
                       if _VIRTUAL_ONLY.search(line) and _EVENT.search(doc.text)), None)
        fee = next((line for line in lines if _FEE.search(line)), None)
        if not online or not fee:
            return None
        fee_document, fee_line, online_line = doc, fee, online
    if fee_document is None:
        return None
    return RuleVerdict(
        rule_id="private_purchase_eligibility", verdict="not_applicable",
        reason=("The submitted receipt identifies only an online-only event "
                "participation fee. The SAP private-purchase exception is outside "
                "this rule's stated subject; the online-event fee rule must "
                "assess the reimbursement route separately."),
        case_quotes=[CaseQuote(document=fee_document.name, quote=online_line),
                     CaseQuote(document=fee_document.name, quote=fee_line)],
    )


# From reimbursement_route_evidence.py
_PRIVATE_PURCHASE_TOPIC = re.compile(r"reimbursement of privately advanced costs", re.I)


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
    if verdict.rule_id != "private_purchase_eligibility" or not _PRIVATE_PURCHASE_TOPIC.search(topic):
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


# From reimbursement_hospitality_evidence.py
_GUEST = re.compile(
    r"\b(?:für|an|mit)\s+(?:externen?\s+)?gäst\w*|"
    r"\b(?:for|with)\s+(?:external\s+)?(?:guests?|visitors?)\b", re.I
)


_STAFF = re.compile(
    r"\b(?:nur|ausschließlich)\s+(?:für\s+)?(?:mitarbeiter\w*|bedienstete\w*|personal)\b|"
    r"\bstaff.only\b", re.I
)


_PANTRY = re.compile(
    r"\b(?:teeküche|personalküche|aufenthaltsraum|staff\s+kitchen|staff\s+pantry|"
    r"break\s+room|kitchenette)\b", re.I
)


_EQUIPMENT = re.compile(r"\b(?:wasserkocher\w*|kaffeebecher\w*|tassen\w*|kettle\w*|mugs?)\b", re.I)


_CONSUMABLE = re.compile(
    r"\b(?:kaffee(?!becher|maschine|küche)\w*|(?:\w*tee|teebeutel)\b|"
    r"coffee|tea|mineralwasser|obst|gebäck|fruit|biscuits?)\b", re.I
)


_EXCLUSION = "bewirtungen, an denen keine externen personen teilgenommen haben"


_COURTESY = "die gästen der universität angeboten werden"


def _downgrade(result: RuleVerdict, reason: str) -> RuleVerdict:
    return result.model_copy(update={
        "verdict": "unknown",
        "reason": (result.reason + f" [Evidence gate: {reason}]").strip(),
    })


def guard_hospitality(
    result: RuleVerdict,
    documents: dict[str, CaseDocument],
) -> tuple[RuleVerdict, tuple[str, ...], str]:
    """Return guarded verdict, issue codes, and evidence strength.

    Model-cited policy spans are already verified against the digest by
    ``_to_verdict``. This function checks their *role* and corroborating
    case content; it does not turn a policy classification into a permission.
    """
    if result.rule_id != "hospitality_and_refreshments":
        return result, (), "not_checked"
    content = "\n".join(doc.text for doc in documents.values())
    cited = "\n".join(q.quote for q in result.case_quotes)
    policy = "\n".join(q.quote for q in result.policy_quotes).casefold()
    guest = bool(_GUEST.search(content))
    issues: list[str] = []
    strength = "unresolved"

    if result.verdict == "fail":
        if guest:
            issues.append("positive_guest_evidence_blocks_internal_only_fail")
        if not _CONSUMABLE.search(cited):
            issues.append("no_cited_consumable_line")
        if _EXCLUSION not in policy:
            issues.append("no_cited_staff_only_exclusion")
        direct_staff = bool(_STAFF.search(content))
        inferred_staff = (
            bool(_PANTRY.search(content)) and bool(_EQUIPMENT.search(content))
            and bool(_PANTRY.search(cited))
        )
        if not direct_staff and not inferred_staff:
            issues.append("no_corroborated_internal_use")
        if issues:
            return _downgrade(result, ",".join(issues)), tuple(issues), strength
        strength = "direct" if direct_staff else "circumstantial"

    elif result.verdict == "not_applicable":
        if _CONSUMABLE.search(content) and not guest:
            issues.append("guest_courtesy_classification_without_guest_evidence")
            return _downgrade(result, issues[0]), tuple(issues), strength

    elif result.verdict == "pass":
        if _COURTESY in policy and not guest:
            issues.append("guest_permission_without_guest_evidence")
        # Event reimbursement has additional funding and participant conditions.
        if "soweit sich in den o. g. fällen" in policy and not re.search(
            r"(?:drittmittelgeber erlaubt|drittmittel.*(?:erlaubt|genehmigt)|"
            r"bewilligte drittmittel|approved.*funding|permitted.*grant)", content, re.I
        ):
            issues.append("event_funding_condition_unverified")
        if _COURTESY in policy and "soweit sich in den o. g. fällen" not in policy:
            issues.append("courtesy_classification_is_not_reimbursement_permission")
        if issues:
            return _downgrade(result, ",".join(issues)), tuple(issues), strength

    return result, tuple(issues), strength
