"""Read the mounted corpora and turn them into passages, cached across runs."""

import asyncio
import gzip
import hashlib
import json
import os
import pickle
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, NamedTuple

from src.config import PASSAGE_CACHE_DIR
from src.text import normalize_text

from .languages import infer_language
from .passages import Passage, split_into_passages

Document = dict[str, Any]

# The passage cache is invalidated whenever the code that produces passages changes.
_PASSAGE_CACHE_SOURCES = [
    Path(__file__).parent / "corpora.py",
    Path(__file__).parent / "languages.py",
    Path(__file__).parent / "passages.py",
    Path(__file__).parent.parent / "config.py",
    Path(__file__).parent.parent / "text.py",
]


class PreparedCorpus(NamedTuple):
    passages: dict[str, Passage]  # passage_id -> passage
    language: str


async def prepare_corpora(
    corpora_root: Path, *, max_workers: int | None = None
) -> dict[str, PreparedCorpus]:
    """Split every corpus under `corpora_root` into passages, one process per corpus."""
    print(f"Preparing corpora from {corpora_root}...")

    start = time.perf_counter()
    loop = asyncio.get_running_loop()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        tasks = [
            loop.run_in_executor(executor, _load_or_prepare_corpus, name, path)
            for name, path in find_corpora(corpora_root).items()
        ]
        results = await asyncio.gather(*tasks)

    print(f"Corpora prepared in {time.perf_counter() - start:.2f}s")
    return dict(results)


def find_corpora(corpora_root: Path) -> dict[str, Path]:
    """Corpus name -> path of its `documents.jsonl.gz`."""
    if not corpora_root.is_dir():
        raise ValueError(f"Corpora directory does not exist in {corpora_root}")

    corpora = {
        documents_path.parent.name: documents_path
        for documents_path in sorted(corpora_root.glob("*/documents.jsonl.gz"))
    }

    if not corpora:
        raise ValueError(f"No corpora found in {corpora_root}")

    return corpora


def read_documents(documents_path: Path) -> list[Document]:
    documents: list[Document] = []

    with gzip.open(documents_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()

            if not line:
                continue

            documents.append(json.loads(line))

    if not documents:
        raise ValueError(f"No documents found in {documents_path}.")

    return documents


def deduplicate_documents(documents: list[Document]) -> list[Document]:
    """Remove empty and exact-content duplicate documents before passage creation and indexing."""
    seen: set[str] = set()
    unique: list[Document] = []

    for document in documents:
        text = document.get("content", "")

        if not isinstance(text, str) or not text.strip():
            continue

        normalized = normalize_text(text)
        fingerprint = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

        if fingerprint in seen:
            continue

        seen.add(fingerprint)
        unique.append(document)

    return unique


def _load_or_prepare_corpus(
    corpus_name: str, documents_path: Path
) -> tuple[str, PreparedCorpus]:
    cache_path = (PASSAGE_CACHE_DIR / f"{corpus_name}.pkl").resolve()
    fingerprint = _corpus_fingerprint(documents_path)

    if cache_path.is_file():
        with cache_path.open("rb") as handle:
            cached_fingerprint, prepared = pickle.load(handle)
        if cached_fingerprint == fingerprint:
            print(f"[{corpus_name}] reusing cached passages")
            return corpus_name, prepared

    prepared = _prepare_corpus(corpus_name, documents_path)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = cache_path.with_suffix(f".{os.getpid()}.tmp")
    with tmp_path.open("wb") as handle:
        pickle.dump((fingerprint, prepared), handle, protocol=pickle.HIGHEST_PROTOCOL)
    # atomic, so an interrupted write is never treated as cached
    tmp_path.replace(cache_path)

    return corpus_name, prepared


def _corpus_fingerprint(documents_path: Path) -> str:
    """Hash of the documents file and of the code that turns it into passages."""
    digest = hashlib.sha256()
    for path in (documents_path, *_PASSAGE_CACHE_SOURCES):
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _prepare_corpus(corpus_name: str, documents_path: Path) -> PreparedCorpus:
    documents = read_documents(documents_path)
    n_original = len(documents)
    documents = deduplicate_documents(documents)
    print(
        f"[{corpus_name}] removed {n_original - len(documents)} empty/duplicate documents"
    )

    if not documents:
        raise ValueError(
            f"Corpus {corpus_name!r} has no documents after deduplication."
        )

    language = infer_language(corpus_name, documents[0])

    passages = {
        passage.passage_id: passage
        for doc in documents
        for passage in split_into_passages(
            corpus_name,
            doc["doc_id"],
            doc["title"],
            doc["content"],
            language,
            normalize=True,
        )
    }
    return PreparedCorpus(passages, language)
