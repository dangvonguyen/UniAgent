import re
import unicodedata
from functools import cache

import pysbd

_INVISIBLE_CHARS_TABLE = dict.fromkeys(map(ord, "\xad\u200b\u200c\u200d\u2060\ufeff"))
_HYPHEN_VARIANTS_TABLE = dict.fromkeys(map(ord, "\u2010\u2011"), "-")
_UNICODE_SPACES = re.compile(r"[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]")
_PARAGRAPH_SEPARATOR = re.compile(r"\u2029")
_LINE_BREAK_VARIANTS = re.compile(r"\r\n|[\r\f\v\x85\u2028]")
_NON_NEWLINE_WHITESPACE = re.compile(r"[^\S\n]+")
_SPACES_AROUND_NEWLINE = re.compile(r" *\n *")
_THREE_OR_MORE_NEWLINES = re.compile(r"\n{3,}")


def normalize_chars(raw_text: str) -> str:
    """Canonical characters (NFC, no invisibles, plain hyphens and spaces); layout untouched."""
    text = unicodedata.normalize("NFC", raw_text)
    text = text.translate(_INVISIBLE_CHARS_TABLE)
    text = text.translate(_HYPHEN_VARIANTS_TABLE)
    return _UNICODE_SPACES.sub(" ", text)


def normalize_text(raw_text: str) -> str:
    """Canonical characters and unified whitespace, keeping blank lines distinct from line breaks."""
    text = normalize_chars(raw_text)
    text = _PARAGRAPH_SEPARATOR.sub("\n\n", text)
    text = _LINE_BREAK_VARIANTS.sub("\n", text)
    text = _NON_NEWLINE_WHITESPACE.sub(" ", text)
    text = _SPACES_AROUND_NEWLINE.sub("\n", text)
    text = _THREE_OR_MORE_NEWLINES.sub("\n\n", text)
    return text.strip()


_SENTENCE_END_MARKS = ".!?…"
_CLOSING_QUOTES_AND_BRACKETS = "\"'”“»«)]"  # may follow an end mark: `He said "stop."`
_OPENING_QUOTES_AND_BRACKETS = "\"'„“«»(["  # non-letters that can start a sentence


def sentence_spans(text: str, language: str) -> list[tuple[int, int]] | None:
    """[start, end) offsets of the sentences in text, or None if pysbd can't be trusted.

    Uses pysbd, then repairs its false breaks after abbreviations ("gem.", "Abs.").
    Whitespace between sentences belongs to no span.
    """
    sentences: list[tuple[int, int]] = []
    search_start = 0  # where to look for the next sentence inside `text`

    for raw_sentence in _get_sentence_segmenter(language).segment(text):
        sentence_text = raw_sentence.strip()
        if not sentence_text:
            continue

        offset = text.find(sentence_text, search_start)
        if offset == -1:  # pysbd changed the text -> can't trust its pieces
            return None
        search_start = offset + len(sentence_text)

        # Keep a break only if the previous piece ends a sentence and this one starts one.
        if sentences and not is_real_sentence_break(text, sentences[-1], offset):
            sentences[-1] = (sentences[-1][0], search_start)
        else:
            sentences.append((offset, search_start))
    return sentences


@cache
def _get_sentence_segmenter(language: str) -> pysbd.Segmenter:
    return pysbd.Segmenter(language=language, clean=False)


def ends_with_sentence_mark(text: str) -> bool:
    text = text.rstrip(_CLOSING_QUOTES_AND_BRACKETS)
    return bool(text) and text[-1] in _SENTENCE_END_MARKS


def is_real_sentence_break(
    text: str, previous_sentence: tuple[int, int], next_start: int
) -> bool:
    previous = text[previous_sentence[0] : previous_sentence[1]]
    next_char = text[next_start]
    return ends_with_sentence_mark(previous) and (
        next_char.isupper() or next_char in _OPENING_QUOTES_AND_BRACKETS
    )
