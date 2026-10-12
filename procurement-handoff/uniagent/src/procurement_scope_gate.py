"""Mechanical provenance and narrow-scope checks shared by procurement rules 1/2.

This does not infer whether an arbitrary policy governs an arbitrary product.
When a quote expressly restricts a provision to a named category, it can
reject an unsupported extension to a packet that never mentions that category.
"""

import re

from .quotes import match_case_quote
from .text import normalize_chars


_CATEGORY = re.compile(
    r"\bF[uü]r\s+([\wäöüÄÖÜß -]{3,65}?)\s+"
    r"(?:existiert|besteht|gilt|gelten|ist|sind)\b", re.I
)
_DIRECT_AWARD = re.compile(r"\b(?:Direktauftrag|Direktvergabe|direct award)\b", re.I)
_STOP = {"konventionelles", "konventionelle", "konventionellen", "einen", "eine",
         "dieses", "diese", "solche", "bestimmte", "bestimmten", "und", "oder"}


def _present(fragment: str, whole: str) -> bool:
    def compact(s):
        return " ".join(normalize_chars(s).lower().split())
    return bool(fragment.strip()) and compact(fragment) in compact(whole)


def _category_terms(quote: str) -> set[str]:
    """Only explicit German category introductions, never a global ontology."""
    matches = _CATEGORY.findall(quote)
    return {word.casefold() for phrase in matches for word in re.findall(r"[\wäöüÄÖÜß]+", phrase)
            if len(word) > 3 and word.casefold() not in _STOP}


def packet_has_applicable_direct_award_quote(policy, documents) -> bool:
    """Conservative retry check: does any method quote plausibly cover this case?

    A method quote with no *explicit* product restriction is kept as possibly
    applicable. This only skips retry when every quote about direct award has
    an express category absent from the case packet (or none mentions it).
    """
    packet = "\n".join(d.text for d in documents.values()).casefold()
    for source in policy.values():
        if not _DIRECT_AWARD.search(source.quote):
            continue
        terms = _category_terms(source.quote)
        if not terms or any(re.search(r"(?<!\w)" + re.escape(t) + r"\w*", packet)
                            for t in terms):
            return True
    return False


def scope_errors(rule_id, links, refs, policy, documents) -> list[str]:
    if not links:
        return ["missing-item-policy-scope-link"]
    errors: list[str] = []
    cited = {r.strip().upper() for r in refs}
    all_case_text = "\n".join(d.text for d in documents.values()).casefold()
    direct_award = rule_id == "comparison_offers" and bool(_DIRECT_AWARD.search(all_case_text))
    method_resolved = False
    linked = set()
    for link in links:
        ref = link.policy_ref.strip().upper()
        source = policy.get(ref)
        doc = documents.get(link.case_source.strip().upper())
        if ref not in cited or source is None:
            errors.append(f"scope-policy-ref-not-cited:{ref}")
            continue
        linked.add(ref)
        if not _present(link.policy_scope, source.quote):
            errors.append(f"scope-text-not-in-policy:{ref}")
        if doc is None or match_case_quote(link.case_item, doc.text) is None:
            errors.append(f"item-text-not-in-case:{ref}")
        terms = _category_terms(source.quote)
        item_text = link.case_item.casefold()
        item_in_scope = not terms or any(
            re.search(r"(?<!\w)" + re.escape(t) + r"\w*", item_text) for t in terms)
        if not item_in_scope:
            errors.append(f"explicit-product-scope-not-established:{ref}")
        if direct_award and _DIRECT_AWARD.search(source.quote) and item_in_scope:
            method_resolved = True
    if direct_award and not method_resolved:
        errors.append("claimed-direct-award-has-no-applicable-method-quote")
    if not linked:
        errors.append("no-valid-item-policy-link")
    return list(dict.fromkeys(errors))


def stage_errors(rule_id, verdict, refs, policy, documents) -> list[str]:
    """Check when an ordering duty attaches to a proposed purchase.

    A request is not an executed order. A policy that expressly governs the
    intent to order, however, may already constrain what can be proposed for
    approval. This check only establishes timing; scope, evidence, and any
    exceptions still need independent verification.
    """
    if rule_id != "framework_contract_sourcing" or verdict != "fail":
        return []
    packet = "\n".join(d.text for d in documents.values())
    cited = "\n".join(policy[r.strip().upper()].quote for r in refs
                       if r.strip().upper() in policy)
    executed = re.search(r"(?i)\b(?:Auftragsbestätigung|Bestellnummer|"
                         r"bereits\s+bestellt|bestellt\s+am|order\s+placed|"
                         r"Rechnung\s+Nr\.)\b", packet)
    request_duty = re.search(r"(?i)\b(?:vor\s+der\s+Bestellung|"
                             r"Beschaffungsformular|bei\s+Beantragung|"
                             r"Bestellanforderung|procurement\s+request|"
                             r"bestell\w*\s+(?:woll\w*|m[oö]cht\w*|soll\w*)|"
                             r"(?:woll\w*|m[oö]cht\w*)\s+[^.]{0,80}\bbestell\w*)\b", cited)
    ordering_duty = re.search(r"(?i)\b(?:bestell\w*|order\w*)\b", cited)
    if not executed and ordering_duty and not request_duty:
        return ["ordering-duty-not-shown-due-at-request-stage"]
    return []
