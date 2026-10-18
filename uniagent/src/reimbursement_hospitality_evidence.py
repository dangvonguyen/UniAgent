"""Conservative source-role gate for the hospitality rule.

The gate never upgrades a model verdict to fail or pass. A fail resting on an
inferred internal pantry use is retained with a circumstantial marker. A
positive guest-purpose statement blocks that inference. Terms are generic
categories, never case identifiers or generated dossier labels.
"""

import re

from .models import CaseDocument, PolicyQuote, RuleVerdict


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
