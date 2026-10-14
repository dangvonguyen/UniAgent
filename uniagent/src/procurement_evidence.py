"""Mechanical floor for procurement rules that need a quoted obligation.

This proves that the stated fact and obligation are present in their cited
sources. It cannot certify semantic scope, exceptions, or legal correctness.
An incomplete chain is a technical rule error, never a business verdict.
"""

from __future__ import annotations

import re

from .quotes import match_case_quote
from .text_utils import norm_ws


# These are concepts, not amounts, vendors, case identifiers or policy limits.
REQUIREMENT_KIND = {
    "amount_calculation": re.compile(
        r"(?i)(?:rechnerisch|rechnerische|richtig|korrekt|zutreffend|"
        r"vollständig|accuracy|correct|calculation|Berechnung)"
        r".{0,100}(?:Betrag|Preis|Summe|Kosten|Angab|amount|price|total)|"
        r"(?:Betrag|Preis|Summe|Kosten|Angab|amount|price|total)"
        r".{0,100}(?:rechnerisch|richtig|korrekt|zutreffend|vollständig|"
        r"accuracy|correct|calculation|Berechnung)"
    ),
    "document_consistency": re.compile(
        r"(?i)(?:richtig|zutreffend|vollständig|übereinstimm|"
        r"nachweis|beleg|accurate|consistent|supporting document)"
        r".{0,100}(?:Antrag|Angebot|Preis|Betrag|Unterlag|Angab|request|offer)|"
        r"(?:Antrag|Angebot|Preis|Betrag|Unterlag|Angab|request|offer)"
        r".{0,100}(?:richtig|zutreffend|vollständig|übereinstimm|"
        r"nachweis|beleg|accurate|consistent|supporting document)"
    ),
    "award_selection": re.compile(
        r"(?i)(?:Zuschlag|Auftragsvergabe|award|ausgewählt|selection)"
        r".{0,120}(?:wirtschaftlich|günstig|niedrig|Kriteri|criterion|"
        r"price|Preis)|(?:wirtschaftlich|günstig|niedrig|Kriteri|"
        r"criterion|price|Preis).{0,120}(?:Zuschlag|Auftragsvergabe|"
        r"award|ausgewählt|selection)"
    ),
}

DISCLOSURE_ONLY = re.compile(
    r"(?i)(?:bekannt\s*zu\s*geben|bekanntmach|offenleg|publizier|"
    r"publish|disclos|communicat)"
)
MANDATORY = re.compile(
    r"(?i)\b(?:muss|müssen|darf|dürfen|hat\b[^.]{0,70}\bzu\b|"
    r"haben\b[^.]{0,70}\bzu\b|ist\b[^.]{0,70}\bzu\b|"
    r"sind\b[^.]{0,70}\bzu\b|must|shall|required)\b"
)
AWARD_DECISION = re.compile(
    r"(?i)(?:Zuschlag\s+(?:ist|muss|soll|darf|erfolgt|wird)|"
    r"(?:award|contract)\s+(?:must|shall|is\s+to|goes\s+to)|"
    r"wirtschaftlichst\w*\s+Angebot\s+\w*\s+(?:Zuschlag|ausgewählt))"
)


def decision_evidence_errors(rule_id, links, refs, policy, documents) -> list[str]:
    """Require a source-backed fact and a relevant operative duty for pass/fail."""
    if not links:
        return ["missing-decision-evidence-link"]
    cited = {ref.strip().upper() for ref in refs}
    kind = REQUIREMENT_KIND.get(rule_id)
    errors: list[str] = []
    for link in links:
        ref = link.policy_ref.strip().upper()
        source = policy.get(ref)
        doc = documents.get(link.case_source.strip().upper())
        if ref not in cited or source is None:
            errors.append(f"evidence-policy-ref-not-cited:{ref}")
            continue
        span = link.policy_obligation.strip()
        if len(norm_ws(span)) < 30 or norm_ws(span) not in norm_ws(source.quote):
            errors.append(f"evidence-obligation-not-in-policy:{ref}")
            continue
        if not MANDATORY.search(span):
            errors.append(f"evidence-no-mandatory-language:{ref}")
        if kind is not None and not kind.search(span):
            errors.append(f"evidence-obligation-kind-not-established:{ref}")
        if (rule_id == "award_selection" and DISCLOSURE_ONLY.search(span)
                and not AWARD_DECISION.search(span)):
            errors.append(f"evidence-only-requires-disclosure:{ref}")
        if not doc or len(norm_ws(link.case_fact)) < 12 or not match_case_quote(
                link.case_fact, doc.text):
            errors.append(f"evidence-fact-not-in-case:{ref}")
        if not link.stage.strip():
            errors.append(f"evidence-stage-missing:{ref}")
    return list(dict.fromkeys(errors))
