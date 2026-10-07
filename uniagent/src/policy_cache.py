"""Content-addressed snapshot of the policy digest used by every case."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from .config import (DIGEST_CONTEXT_K, DIGEST_MAX_DOC_CHARS,
                     RETRIEVAL_DEPTH, RETRIEVAL_RRF_K)
from .models import ResolvedRule, Rule

VERSION = 1
SOURCE_DIR = Path(__file__).resolve().parent


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def signature(corpora: Path, rules: list[Rule], model: str,
              endpoint: str, max_tokens: int) -> str:
    """Invalidate when the corpus, retrieval, selector or model setup changes."""
    if not corpora.is_dir():
        raise ValueError(f"Policy corpus directory is missing: {corpora}")
    files = sorted(p for p in corpora.rglob("*") if p.is_file())
    if not files:
        raise ValueError(f"Policy corpus has no files: {corpora}")
    source_files = [SOURCE_DIR / "digest.py", SOURCE_DIR / "config.py",
                    SOURCE_DIR / "llm.py", *sorted((SOURCE_DIR / "retrieval").glob("*.py"))]
    manifest = {
        "version": VERSION,
        "corpus": [(p.relative_to(corpora).as_posix(), _hash_file(p)) for p in files],
        "rules": [r.model_dump(mode="json") for r in rules],
        "source": [(p.relative_to(SOURCE_DIR).as_posix(), _hash_file(p))
                   for p in source_files],
        "settings": {"context_k": DIGEST_CONTEXT_K,
                     "max_doc_chars": DIGEST_MAX_DOC_CHARS,
                     "retrieval_depth": RETRIEVAL_DEPTH, "rrf_k": RETRIEVAL_RRF_K,
                     "model": model, "endpoint_hash": hashlib.sha256(
                         endpoint.encode("utf-8")).hexdigest(),
                     "max_tokens": max_tokens},
    }
    return hashlib.sha256(_canonical(manifest)).hexdigest()


def load(path: Path, expected_signature: str, rules: list[Rule]) -> list[ResolvedRule]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read policy digest cache {path}: {exc}") from exc
    if data.get("version") != VERSION or data.get("signature") != expected_signature:
        raise ValueError("Policy digest cache is stale. Rebuild it explicitly with "
                         "--refresh-policy-cache; do not compare runs with different inputs.")
    payload = data.get("rules")
    if not isinstance(payload, list) or data.get("content_sha256") != hashlib.sha256(
            _canonical(payload)).hexdigest():
        raise ValueError("Policy digest cache content is incomplete or modified")
    resolved = [ResolvedRule.model_validate(item) for item in payload]
    if [item.rule.model_dump(mode="json") for item in resolved] != [
            item.model_dump(mode="json") for item in rules]:
        raise ValueError("Policy digest cache rule list differs from the current rules")
    return resolved


def save(path: Path, cache_signature: str, rules: list[ResolvedRule]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [rule.model_dump(mode="json") for rule in rules]
    data = {"version": VERSION, "signature": cache_signature, "rules": payload,
            "content_sha256": hashlib.sha256(_canonical(payload)).hexdigest()}
    fd, temp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
