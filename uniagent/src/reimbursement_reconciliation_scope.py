"""Case-independent activation test for expense reconciliation.

This test only determines whether a cost comparison is needed. It never
decides whether an invoice is valid or whether a claimant paid personally.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass


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
