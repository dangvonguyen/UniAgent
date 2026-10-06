import re
import unicodedata

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
