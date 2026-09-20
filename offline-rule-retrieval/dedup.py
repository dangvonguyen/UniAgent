import hashlib
import re
from typing import Any


def normalize_text(text: str) -> str:
    """Normalize text before exact-duplicate comparison."""
    text = text.casefold()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def text_fingerprint(text: str) -> str:
    """Return a stable hash for normalized text."""
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def deduplicate_exact(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove candidates with identical normalized text.

    The first occurrence is kept. Provenance of later duplicates is
    recorded in `duplicate_sources`.
    """

    seen: dict[str, dict[str, Any]] = {}
    unique: list[dict[str, Any]] = []

    for candidate in candidates:
        text = candidate.get("text", "")

        if not isinstance(text, str) or not text.strip():
            kept = dict(candidate)
            kept.setdefault("duplicate_sources", [])
            unique.append(kept)
            continue

        fingerprint = text_fingerprint(text)

        if fingerprint not in seen:
            kept = dict(candidate)
            kept["duplicate_sources"] = []
            seen[fingerprint] = kept
            unique.append(kept)
            continue

        seen[fingerprint]["duplicate_sources"].append(
            {
                "corpus": candidate.get("corpus"),
                "doc_id": candidate.get("doc_id"),
                "chunk_id": candidate.get("chunk_id"),
            }
        )

    return unique
