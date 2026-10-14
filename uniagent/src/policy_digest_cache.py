"""Validated corpus/rule/model scoped cache for policy quote packets."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .config import CACHE_DIR
from .models import PolicyQuote, ResolvedRule, Rule

CACHE_VERSION = 1
CODE_FILES = (
    "config.py", "digest.py", "policy_digest_cache.py", "quotes.py", "models.py",
    "retrieval/corpora.py", "retrieval/index.py", "retrieval/lexical.py",
    "retrieval/dense.py", "retrieval/fusion.py", "retrieval/passages.py",
)


def corpus_signature(root: Path) -> str:
    """Full content hash: a changed corpus or retrieval implementation invalidates packets."""
    h = hashlib.sha256()
    files = sorted(root.glob("*/documents.jsonl.gz"))
    if not files:
        raise ValueError(f"No corpus documents in {root}")
    for path in files:
        name = path.parent.name
        h.update(name.encode()); h.update(b"\0")
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        h.update(b"\0")
    src = Path(__file__).resolve().parent
    for relative in CODE_FILES:
        h.update(relative.encode()); h.update(b"\0")
        h.update((src / relative).read_bytes()); h.update(b"\0")
    return h.hexdigest()


def cache_path(rule: Rule, topic: str, signature: str, model: str) -> Path:
    payload = {"version": CACHE_VERSION, "signature": signature, "model": model,
               "topic": topic, "rule": rule.model_dump(mode="json")}
    key = hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return CACHE_DIR / "policy-digests" / f"{rule.id}-{key}.json"


def load(rule: Rule, topic: str, signature: str, model: str) -> ResolvedRule | None:
    path = cache_path(rule, topic, signature, model)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        entry = ResolvedRule.model_validate(data)
        if entry.rule != rule or entry.error:
            return None
        return entry
    except (OSError, ValueError):
        return None


def save(entry: ResolvedRule, topic: str, signature: str, model: str) -> None:
    if entry.error:
        return
    path = cache_path(entry.rule, topic, signature, model)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    try:
        tmp.write_text(entry.model_dump_json(), encoding="utf-8")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)
