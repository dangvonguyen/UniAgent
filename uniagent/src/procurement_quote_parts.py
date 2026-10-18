"""Verify separated PDF citations without inventing a joined source span."""
import re
from .quotes import match_case_quote, _locate
from .text import normalize_text

def match_case_parts(quote: str | None, source: str) -> list[str]:
    """Recover a short ellipsis citation as separate, real PDF excerpts.

    Each part must match exactly after character/whitespace normalization,
    occur in order, and lie within a six-line window. We never join the
    pieces into a fabricated contiguous quotation.
    """
    direct = match_case_quote(quote, source)
    if direct is not None:
        return [direct]
    if not quote or not re.search(r"(?:\.\.\.|…)", quote):
        return []
    parts = re.split(r"(?:\.\.\.|…)", quote)
    if not 2 <= len(parts) <= 3 or any(
            sum(c.isalnum() for c in part) < 14 for part in parts):
        return []
    text = normalize_text(source)
    found = []
    last = 0
    first = None
    for part in parts:
        span = _locate(part, text, keep=str.isalnum, fuzzy=False)
        if span is None or span[0] < last:
            return []
        if first is None:
            first = span[0]
        if text[first:span[1]].count("\n") > 6:
            return []
        found.append(text[span[0]:span[1]])
        last = span[1]
    return found

