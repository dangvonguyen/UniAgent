"""Tiny shared helpers (kept separate from src/text.py to avoid touching it)."""


def norm_ws(s: str) -> str:
    return " ".join(s.split()).casefold()
