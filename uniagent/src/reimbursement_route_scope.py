"""Identify a narrow, document-supported exception to the SAP purchase rule.

The private-purchase rule expressly excludes online-event fees. This classifier
only identifies an unambiguous, fee-only virtual event claim. It makes no
decision about whether the fee itself is reimbursable; that remains with the
online-event fee rule and the other reimbursement checks.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

from .models import CaseDocument, CaseQuote, RuleVerdict


_TOPIC = re.compile(r"reimbursement of privately advanced costs", re.I)
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
    if not _TOPIC.search(topic):
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
