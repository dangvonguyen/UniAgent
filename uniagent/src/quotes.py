"""Quote verification: tying a model's quote to the exact text of its source."""

from collections.abc import Callable

from rapidfuzz import fuzz
from rapidfuzz.distance import Indel

from .config import (
    QUOTE_MATCH_MIN_CHARS,
    QUOTE_MATCH_MIN_RUN,
    QUOTE_MATCH_MIN_SCORE,
    QUOTE_MAX_WIDEN_CHARS,
)
from .text import normalize_text, sentence_spans


def match_policy_quote(quote: str | None, source: str, language: str) -> str | None:
    """The source's own text for a policy quote, widened to whole sentences, or None."""
    text = normalize_text(source)
    span = _locate(quote, text, keep=lambda c: not c.isspace(), fuzzy=True)
    if span is None:
        return None
    first, last = _widen_to_sentences(text, *span, language)
    return text[first:last]


def match_case_quote(quote: str | None, source: str) -> str | None:
    """The source's own text for a case quote, or None."""
    text = normalize_text(source)
    span = _locate(quote, text, keep=str.isalnum, fuzzy=False)
    return None if span is None else text[span[0] : span[1]]


def _locate(
    quote: str, text: str, *, keep: Callable[[str], bool], fuzzy: bool
) -> tuple[int, int] | None:
    """[first, last) of the quote in text."""
    needle, _ = _compact(normalize_text(quote), keep)
    haystack, offsets = _compact(text, keep)
    if not needle:
        return None

    start = haystack.find(needle)
    if start >= 0:
        end = start + len(needle)
    elif fuzzy and len(needle) >= QUOTE_MATCH_MIN_CHARS:
        alignment = fuzz.partial_ratio_alignment(
            needle, haystack, score_cutoff=QUOTE_MATCH_MIN_SCORE
        )
        if alignment is None:
            return None
        start, end = _trim_to_matches(
            needle, haystack, alignment.dest_start, alignment.dest_end
        )
    else:
        return None
    return offsets[start], offsets[end - 1] + 1


def _widen_to_sentences(
    text: str, first: int, last: int, language: str
) -> tuple[int, int]:
    """Extend [first, last) to the sentences it touches; line breaks also end sentences."""
    line_start = text.rfind("\n", 0, first) + 1
    line_end = text.find("\n", last)
    line_end = len(text) if line_end == -1 else line_end
    region = text[line_start:line_end]
    sentences = sentence_spans(region, language) or [(0, len(region))]

    touched = [
        (line_start + start, line_start + end)
        for start, end in sentences
        if line_start + start < last and line_start + end > first
    ]
    new_first = touched[0][0] if touched else first
    new_last = touched[-1][1] if touched else last

    if first - new_first > QUOTE_MAX_WIDEN_CHARS:
        new_first = first
        while new_first > 0 and text[new_first - 1].isalnum():
            new_first -= 1
    if new_last - last > QUOTE_MAX_WIDEN_CHARS:
        new_last = last
        while new_last < len(text) and text[new_last].isalnum():
            new_last += 1
    return min(new_first, first), max(new_last, last)


def _trim_to_matches(
    needle: str, haystack: str, start: int, end: int
) -> tuple[int, int]:
    """Narrow an aligned window to the span between its first and last real match."""
    margin = len(needle) // 5
    lo, hi = max(0, start - margin), min(len(haystack), end + margin)
    runs = [
        op
        for op in Indel.opcodes(needle, haystack[lo:hi])
        if op.tag == "equal" and op.dest_end - op.dest_start >= QUOTE_MATCH_MIN_RUN
    ]
    if not runs:
        return start, end
    return lo + runs[0].dest_start, lo + runs[-1].dest_end


def _compact(text: str, keep: Callable[[str], bool]) -> tuple[str, list[int]]:
    """The kept characters, lowercased, and each one's offset in text."""
    chars: list[str] = []
    offsets: list[int] = []
    for i, char in enumerate(text):
        if keep(char):
            for lowered in char.lower():  # lower() can return more than one char
                chars.append(lowered)
                offsets.append(i)
    return "".join(chars), offsets
