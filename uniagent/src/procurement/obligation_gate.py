"""Mechanical floor for 'obligation quote -> verdict' links (procurement rules 2-5).

A quote may only back a pass/fail when its cited span (a) states a duty
(deontic marker) and (b) is about the kind of duty being claimed. Vocabulary
below is generic legal wording, never case data. Passing this gate is
necessary, not sufficient: scope, stage and the quote-to-fact bridge still
need the scope gate / review.
"""

from __future__ import annotations

import re

from .text_utils import norm_ws

DEONTIC = re.compile(
    r"(?i)\b(muss|müssen|ist\b[^.]{0,60}\bzu\b|sind\b[^.]{0,60}\bzu\b|"
    r"hat\b[^.]{0,60}\bzu\b|haben\b[^.]{0,60}\bzu\b|darf|dürfen|soll|sollen|"
    r"must|shall|required)\b"
)

OBLIGATION_KINDS: dict[str, re.Pattern[str]] = {
    "min_offers": re.compile(
        r"(?i)\b(?:\d+|ein|zwei|drei|vier|fünf|sechs)\s+(?:schriftliche\w*\s+)?Angebot"
    ),
    "lowest_price_award": re.compile(
        r"(?i)(niedrigst|günstigst|wirtschaftlichst|lowest|most economical)"
    ),
    "framework_sourcing": re.compile(r"(?i)(Rahmenvertrag|framework (?:contract|agreement))"),
}


def obligation_errors(kind: str, span: str, policy_quote: str) -> list[str]:
    """Empty list = the span is a verbatim duty of the claimed kind."""
    pattern = OBLIGATION_KINDS.get(kind)
    if pattern is None:
        return [f"unknown-obligation-kind:{kind}"]
    errors: list[str] = []
    if not span.strip() or norm_ws(span) not in norm_ws(policy_quote):
        errors.append("obligation-span-not-in-policy")
    if not DEONTIC.search(span):
        errors.append("no-deontic-marker")
    if not pattern.search(span):
        errors.append("obligation-kind-not-in-span")
    return errors
