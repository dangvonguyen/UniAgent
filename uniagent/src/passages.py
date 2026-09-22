"""Split corpus documents into passages: the unit that is indexed, retrieved and cited.

How one document becomes passages:

1. Normalize   - remove invisible characters and tidy up whitespace.
2. Break down  - cut up blocks that are too long: paragraphs first, then lines,
                 then sentences. Blocks that already fit are left alone.
3. Join        - attach short or unfinished blocks to the block after them.
4. Pack        - group the units into passages of about PASSAGE_TARGET_CHARS,
                 then fix a last passage that came out too short.

All positions (`Span`) are character offsets into the *normalized* text. To map
a passage back to its source, call `normalize_text(raw_text)` first.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from typing import NamedTuple

import pysbd

from .config import (
    PASSAGE_MAX_CHARS,
    PASSAGE_MIN_STANDALONE_BLOCK_CHARS,
    PASSAGE_TAIL_MIN_CHARS,
    PASSAGE_TARGET_CHARS,
)


class Span(NamedTuple):
    """A range [start, end) of characters in the normalized document body."""

    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start


SpanGroup = list[Span]  # neighbouring spans that will become one passage

# --- Text cleaning ---------------------------------------------------------

_INVISIBLE_CHARS_TABLE = dict.fromkeys(map(ord, "\xad\u200b\u200c\u200d\u2060\ufeff"))
_PARAGRAPH_SEPARATOR = re.compile(r"\u2029")
_LINE_BREAK_VARIANTS = re.compile(r"\r\n|[\r\f\v\x85\u2028]")
_NON_NEWLINE_WHITESPACE = re.compile(r"[^\S\n]+")
_SPACES_AROUND_NEWLINE = re.compile(r" *\n *")
_THREE_OR_MORE_NEWLINES = re.compile(r"\n{3,}")

# --- Sentence rules --------------------------------------------------------

_SENTENCE_END_MARKS = ".!?…"
_CLOSING_QUOTES_AND_BRACKETS = "\"'”“»«)]"  # may follow an end mark: `He said "stop."`
_OPENING_QUOTES_AND_BRACKETS = "\"'„“«»(["  # non-letters that can start a sentence


@dataclass(frozen=True)
class Passage:
    corpus: str
    doc_id: str
    index: int  # position of this passage within the document (0, 1, 2, ...)
    start_char: int  # where the passage starts in the normalized document body
    end_char: int  # where it ends (exclusive)
    title: str
    text: str  # the passage text, without the title

    @property
    def passage_id(self) -> str:
        return f"{self.doc_id}#{self.index}"


def normalize_text(raw_text: str) -> str:
    """Remove invisible characters and unify whitespace, keeping blank lines distinct from line breaks."""
    text = unicodedata.normalize("NFC", raw_text).translate(_INVISIBLE_CHARS_TABLE)
    text = _PARAGRAPH_SEPARATOR.sub("\n\n", text)
    text = _LINE_BREAK_VARIANTS.sub("\n", text)
    text = _NON_NEWLINE_WHITESPACE.sub(" ", text)
    text = _SPACES_AROUND_NEWLINE.sub("\n", text)
    text = _THREE_OR_MORE_NEWLINES.sub("\n\n", text)
    return text.strip()


def split_into_passages(
    corpus: str,
    doc_id: str,
    title: str,
    text: str,
    language: str,
    *,
    normalize: bool = False,
) -> list[Passage]:
    """Turn one document into an ordered list of passages."""
    body = text
    if normalize:
        body = normalize_text(text)

    if not body:
        return []

    blocks = _break_into_blocks(body, language)
    units = _join_fragments(body, blocks)
    spans = _pack_into_passages(units)

    return [
        Passage(
            corpus=corpus,
            doc_id=doc_id,
            index=index,
            start_char=span.start,
            end_char=span.end,
            title=title,
            text=body[span.start : span.end],
        )
        for index, span in enumerate(spans)
    ]


# ---------------------------------------------------------------------------
# Step 2: break down
# ---------------------------------------------------------------------------


def _break_into_blocks(body: str, language: str) -> list[Span]:
    """Cut the body into blocks, splitting only the blocks that are too long.

    Boundaries are tried from big to small: paragraph, line, sentence.
    A block that already fits in MAX_PASSAGE_CHARS is never split further.
    A single sentence that is still too long is kept whole.
    """
    splitters: list[Callable[[Span], list[Span]]] = [
        lambda span: _split_at_separator(body, span, "\n\n"),  # paragraphs
        lambda span: _split_at_separator(body, span, "\n"),  # lines
        lambda span: _split_into_sentences(body, span, language),  # sentences
    ]

    blocks = [Span(0, len(body))]
    for split in splitters:
        smaller_blocks: list[Span] = []
        for block in blocks:
            if block.length > PASSAGE_MAX_CHARS:
                smaller_blocks.extend(split(block))
            else:
                smaller_blocks.append(block)
        blocks = smaller_blocks
    return blocks


def _split_at_separator(body: str, span: Span, separator: str) -> list[Span]:
    """Cut a span at every `separator`; the separators themselves are dropped."""
    pieces: list[Span] = []
    piece_start = span.start
    while (separator_pos := body.find(separator, piece_start, span.end)) != -1:
        pieces.append(Span(piece_start, separator_pos))
        piece_start = separator_pos + len(separator)
    pieces.append(Span(piece_start, span.end))
    return [piece for piece in pieces if piece.length > 0]


@cache
def _get_sentence_segmenter(language: str) -> pysbd.Segmenter:
    return pysbd.Segmenter(language=language, clean=False)


def _split_into_sentences(body: str, span: Span, language: str) -> list[Span]:
    """Split a span into sentences using pysbd, then repair its false breaks."""
    chunk = body[span.start : span.end]
    sentences: list[Span] = []
    search_start = 0  # where to look for the next sentence inside `chunk`

    for raw_sentence in _get_sentence_segmenter(language).segment(chunk):
        sentence_text = raw_sentence.strip()
        if not sentence_text:
            continue

        sentence_offset = chunk.find(sentence_text, search_start)
        if sentence_offset == -1:  # pysbd changed the text -> can't trust its pieces
            return [span]
        search_start = sentence_offset + len(sentence_text)
        this_sentence = Span(span.start + sentence_offset, span.start + search_start)

        # pysbd also breaks after abbreviations ("gem.", "Abs."). Keep a break
        # only if the previous piece ends a sentence and this one starts one.
        if sentences and not _is_real_sentence_break(
            body, sentences[-1], this_sentence
        ):
            sentences[-1] = _join_spans(sentences[-1], this_sentence)
        else:
            sentences.append(this_sentence)
    return sentences


def _is_real_sentence_break(
    body: str, previous_sentence: Span, next_sentence: Span
) -> bool:
    return _ends_with_sentence_mark(body, previous_sentence) and _can_start_sentence(
        body[next_sentence.start]
    )


def _ends_with_sentence_mark(body: str, span: Span) -> bool:
    text = body[span.start : span.end].rstrip(_CLOSING_QUOTES_AND_BRACKETS)
    return bool(text) and text[-1] in _SENTENCE_END_MARKS


def _can_start_sentence(char: str) -> bool:
    return char.isupper() or char in _OPENING_QUOTES_AND_BRACKETS


# ---------------------------------------------------------------------------
# Step 3: join
# ---------------------------------------------------------------------------


def _join_fragments(body: str, blocks: list[Span]) -> list[Span]:
    """Attach fragments (short or unfinished blocks) to the block that follows.

    Blocks are collected in `pending_unit` until one of them is a complete
    block, which closes the unit. A unit is also closed early if adding the
    next block would make it longer than MAX_PASSAGE_CHARS.
    """
    units: list[Span] = []
    pending_unit: Span | None = None

    for block in blocks:
        if (
            pending_unit is not None
            and block.end - pending_unit.start > PASSAGE_MAX_CHARS
        ):
            units.append(pending_unit)
            pending_unit = None

        pending_unit = (
            block if pending_unit is None else _join_spans(pending_unit, block)
        )

        if not _is_fragment(body, block):
            units.append(pending_unit)
            pending_unit = None

    if pending_unit is not None:  # fragments left at the end of the document
        if units and pending_unit.end - units[-1].start <= PASSAGE_MAX_CHARS:
            units[-1] = _join_spans(units[-1], pending_unit)  # join backward if it fits
        else:
            units.append(pending_unit)
    return units


def _is_fragment(body: str, block: Span) -> bool:
    """A block that is too short, or stops mid-sentence, belongs with what follows."""
    return (
        block.length < PASSAGE_MIN_STANDALONE_BLOCK_CHARS
        or not _ends_with_sentence_mark(body, block)
    )


# ---------------------------------------------------------------------------
# Step 4: pack
# ---------------------------------------------------------------------------


def _pack_into_passages(units: list[Span]) -> list[Span]:
    """Group units into passages of about TARGET_PASSAGE_CHARS."""
    groups: list[SpanGroup] = []
    for unit in units:
        if groups and unit.end - groups[-1][0].start <= PASSAGE_TARGET_CHARS:
            groups[-1].append(unit)
        else:
            groups.append([unit])

    if len(groups) >= 2 and _group_length(groups[-1]) < PASSAGE_TAIL_MIN_CHARS:
        groups[-2:] = _fix_short_last_passage(groups[-2], groups[-1])

    return [_join_spans(group[0], group[-1]) for group in groups]


def _fix_short_last_passage(
    previous_group: SpanGroup, last_group: SpanGroup
) -> list[SpanGroup]:
    """Deal with a last group that is too short.

    1. If both groups fit in MAX_PASSAGE_CHARS together, merge them.
    2. Otherwise, re-cut them at the unit boundary that makes the smaller
       side as big as possible (both sides must stay within the max).
    3. If no cut is better than what we have, keep the groups as they are.
    """
    combined = previous_group + last_group
    if _group_length(combined) <= PASSAGE_MAX_CHARS:
        return [combined]

    best_split = [previous_group, last_group]
    best_smaller_size = min(_group_length(previous_group), _group_length(last_group))

    for cut in range(1, len(combined)):
        left, right = combined[:cut], combined[cut:]
        left_length, right_length = _group_length(left), _group_length(right)
        if max(left_length, right_length) > PASSAGE_MAX_CHARS:
            continue
        if min(left_length, right_length) > best_smaller_size:
            best_split = [left, right]
            best_smaller_size = min(left_length, right_length)
    return best_split


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _join_spans(first: Span, last: Span) -> Span:
    """The span from the start of `first` to the end of `last` (gaps included)."""
    return Span(first.start, last.end)


def _group_length(group: SpanGroup) -> int:
    return _join_spans(group[0], group[-1]).length
