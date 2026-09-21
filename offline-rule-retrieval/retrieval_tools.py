import gzip
import json
import re
import tempfile
import time
from pathlib import Path
from typing import Any

import pandas as pd
import pyterrier as pt
from smolagents import Tool

from event_logging import log_tool_calls

# Same indexing configuration as ../retrieval-baseline-pyterrier/baseline.py: a
# language-specific stemmer, stopword list, and tokeniser per corpus language.
RETRIEVAL_LANGUAGE_CONFIGURATION = {
    "de": {
        "stemmer": pt.TerrierStemmer.german,
        "stopwords": Path(__file__)
        .with_name("german-stopwords.txt")
        .read_text(encoding="utf-8")
        .splitlines(),
        "tokeniser": pt.TerrierTokeniser.utf,
    },
    "en": {
        "stemmer": pt.TerrierStemmer.porter,
        "stopwords": pt.TerrierStopwords.terrier,
        "tokeniser": pt.TerrierTokeniser.english,
    },
}

# Human-readable descriptions for corpora that are known at the time of writing.
# The dataset README documents that the final test set may ship additional or
# larger corpora (for instance an intranet crawl); build_retrieval_tools()
# therefore discovers corpora at runtime instead of hard-coding this list, and
# falls back to a generic description for anything not listed here.
CORPUS_DESCRIPTIONS = {
    "hessian-law-de": (
        "Public crawl of hessenrecht.hessen.de: German court rulings and decisions "
        "(Urteile, Beschluesse). Useful for legal precedent on travel-expense disputes."
    ),
    "university-kassel-public-de": (
        "Public web crawl of the University of Kassel, German-language pages. Useful "
        "for official public information on travel and reimbursement procedures."
    ),
    "university-kassel-public-en": (
        "Public web crawl of the University of Kassel, English-language pages. Useful "
        "for official public information on travel and reimbursement procedures."
    ),
}


def discover_corpora(input_root: Path) -> dict[str, Path]:
    """Find every retrieval-corpora/<name>/documents.jsonl.gz below input_root."""
    corpora_root = input_root / "retrieval-corpora"
    if not corpora_root.is_dir():
        return {}
    return {
        documents_path.parent.name: documents_path
        for documents_path in sorted(corpora_root.glob("*/documents.jsonl.gz"))
    }


def read_documents(documents_path: Path) -> list[dict[str, Any]]:
    documents = []
    with gzip.open(documents_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            documents.append(json.loads(line))
    if not documents:
        raise ValueError(f"No documents found in {documents_path}.")
    return documents


def document_text(document: dict[str, Any]) -> str:
    text = document.get("content") or document.get("text") or ""

    if not isinstance(text, str) or not text.strip():
        raise ValueError(
            f"Document {document.get('doc_id')!r} has no text content."
        )

    return text

def _word_count(text: str) -> int:
    return len(text.split())


def _split_sentences(
    text: str,
    max_words: int,
) -> list[str]:
    """Split long text by sentence boundaries.

    Hard word splitting is only used when a single sentence itself
    is longer than max_words.
    """

    sentences = [
        sentence.strip()
        for sentence in re.split(
            r"(?<=[.!?])\s+",
            text.strip(),
        )
        if sentence.strip()
    ]

    units: list[str] = []

    for sentence in sentences:
        words = sentence.split()

        if len(words) <= max_words:
            units.append(sentence)
            continue

        # Last resort: one sentence itself is extremely long.
        for start in range(0, len(words), max_words):
            units.append(
                " ".join(
                    words[start:start + max_words]
                )
            )

    return units


def _structural_units(
    text: str,
    max_words: int,
) -> list[str]:
    """Split text using increasingly finer structural boundaries.

    Priority:
    1. blank line (\\n\\n)
    2. single newline (\\n)
    3. sentence boundary
    4. hard word split as last resort
    """

    paragraphs = [
        part.strip()
        for part in re.split(
            r"\n\s*\n+",
            text.strip(),
        )
        if part.strip()
    ]

    units: list[str] = []

    for paragraph in paragraphs:

        if _word_count(paragraph) <= max_words:
            units.append(paragraph)
            continue

        # Paragraph is too large: try single newlines.
        lines = [
            line.strip()
            for line in paragraph.splitlines()
            if line.strip()
        ]

        if len(lines) > 1:
            for line in lines:
                if _word_count(line) <= max_words:
                    units.append(line)
                else:
                    units.extend(
                        _split_sentences(
                            line,
                            max_words,
                        )
                    )
        else:
            # Still too large: split by sentence.
            units.extend(
                _split_sentences(
                    paragraph,
                    max_words,
                )
            )

    return units


def _overlap_units(
    units: list[str],
    max_overlap_words: int,
) -> list[str]:
    """Keep complete trailing structural units as overlap."""

    overlap: list[str] = []
    word_count = 0

    for unit in reversed(units):
        unit_words = _word_count(unit)

        if (
            word_count + unit_words
            > max_overlap_words
        ):
            break

        overlap.insert(0, unit)
        word_count += unit_words

    return overlap


def chunk_document(
    document: dict[str, Any],
    target_size: int = 800,
    max_size: int = 1000,
    overlap_size: int = 150,
) -> list[dict[str, Any]]:
    """Split a document into structure-aware chunks.

    Chunks target roughly 800 words and never intentionally exceed
    1000 words. Boundaries are chosen from paragraphs, lines, and
    sentences before falling back to hard word splitting.
    """

    if target_size <= 0:
        raise ValueError(
            "target_size must be greater than 0."
        )

    if max_size < target_size:
        raise ValueError(
            "max_size must be >= target_size."
        )

    if overlap_size < 0:
        raise ValueError(
            "overlap_size must be >= 0."
        )

    text = document_text(document)

    units = _structural_units(
        text,
        max_words=max_size,
    )

    chunks: list[dict[str, Any]] = []

    current_units: list[str] = []
    current_words = 0
    chunk_index = 0

    def emit_chunk() -> None:
        nonlocal chunk_index

        if not current_units:
            return

        chunk_text = "\n\n".join(
            current_units
        ).strip()

        chunks.append(
            {
                "chunk_id": (
                    f"{document['doc_id']}"
                    f"__{chunk_index:04d}"
                ),
                "doc_id": str(
                    document["doc_id"]
                ),
                "text": chunk_text,
                "title": document.get("title"),
                "url": document.get("url"),
            }
        )

        chunk_index += 1

    for unit in units:
        unit_words = _word_count(unit)

        # Finish the current chunk before adding the next unit
        # if the target is already reached, or adding it would
        # exceed the hard maximum.
        if current_units and (
            current_words >= target_size
            or current_words + unit_words > max_size
        ):
            previous_units = list(
                current_units
            )

            emit_chunk()

            current_units = _overlap_units(
                previous_units,
                overlap_size,
            )

            current_words = sum(
                _word_count(item)
                for item in current_units
            )

        current_units.append(unit)
        current_words += unit_words

    if current_units:
        emit_chunk()

    return chunks


def infer_language(corpus_name: str, sample_document: dict[str, Any]) -> str:
    if corpus_name.endswith("-de"):
        return "de"
    if corpus_name.endswith("-en"):
        return "en"
    language = str(sample_document.get("language", "")).strip().casefold()
    if language in RETRIEVAL_LANGUAGE_CONFIGURATION:
        return language
    raise ValueError(
        f"Cannot infer a supported language for corpus {corpus_name!r}; "
        "expected a '-de'/'-en' folder suffix or a 'language' document field."
    )


def build_index(documents: list[dict[str, Any]], language: str):
    if language not in RETRIEVAL_LANGUAGE_CONFIGURATION:
        raise ValueError(f"Unsupported corpus language: {language}")

    index_directory = Path(
        tempfile.mkdtemp(prefix="business-trip-retrieval-index_")
    )

    indexer = pt.IterDictIndexer(
        str(index_directory.resolve()),
        overwrite=True,
        meta={"docno": 100},
        verbose=False,
        **RETRIEVAL_LANGUAGE_CONFIGURATION[language],
    )

    chunks = []

    for document in documents:
        chunks.extend(chunk_document(document))

    chunks_to_index = (
        {
            "docno": chunk["chunk_id"],
            "text": chunk["text"],
        }
        for chunk in chunks
    )

    index_ref = indexer.index(chunks_to_index)

    return pt.IndexFactory.of(index_ref), chunks


def _best_snippet(text: str, terms: list[str], context_lines: int = 1) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return text[:280].strip()
    best_index, best_score = 0, -1
    for index, line in enumerate(lines):
        folded = line.casefold()
        score = sum(folded.count(term) for term in terms)
        if score > best_score:
            best_index, best_score = index, score
    start = max(0, best_index - context_lines)
    end = min(len(lines), best_index + context_lines + 1)
    return " ".join(part.strip() for part in lines[start:end])


class CorpusRetrievalTool(Tool):
    """Retrieval tool bound to exactly one corpus, built once and reused across cases.

    name/description/inputs are set as class attributes per corpus by
    build_retrieval_tools() (via a dynamic subclass), following the same
    pattern as the static class-level Tool attributes in business_trip_tools.py.
    """

    output_type = "string"

    def __init__(
        self,
        corpus_name: str,
        chunks_by_id: dict[str, dict[str, Any]],
        index: Any,
        language: str,
    ):
        super().__init__()
        self.corpus_name = corpus_name
        self.chunks_by_id = chunks_by_id
        self.index = index
        self.language = language
        self.tokeniser = pt.TerrierTokeniser.java_tokeniser(
            RETRIEVAL_LANGUAGE_CONFIGURATION[language]["tokeniser"]
        )
        self.retriever = pt.terrier.Retriever(index, wmodel="BM25")

    def forward(self, query: str, max_results: int = 5) -> str:
        if not query.strip():
            raise ValueError("query must not be empty.")
        if max_results is None:
            max_results = 5
        if not 1 <= max_results <= 20:
            raise ValueError("max_results must be between 1 and 20.")

        tokenised_query = " ".join(self.tokeniser.getTokens(query))
        if not tokenised_query.strip():
            return json.dumps([], ensure_ascii=False)

        topics = pd.DataFrame([{"qid": "1", "query": tokenised_query}])
        results = self.retriever.transform(topics).sort_values("rank").head(max_results)

        terms = [term.casefold() for term in re.findall(r"\w+", query) if len(term) > 1]
        hits = []
        for _, row in results.iterrows():
            chunk = self.chunks_by_id.get(str(row["docno"]))
            if chunk is None:
                continue
            hits.append(
                {
                    "corpus": self.corpus_name,
                    "doc_id": chunk["doc_id"],
                    "chunk_id": chunk["chunk_id"],
                    "score": float(row["score"]),
                    "title": chunk.get("title"),
                    "url": chunk.get("url"),
                    "text": chunk["text"],
                    "snippet": _best_snippet(chunk["text"], terms),
                }
            )
        return json.dumps(hits, ensure_ascii=False)


def _tool_class_name(corpus_name: str) -> str:
    return "Retrieve" + "".join(part.capitalize() for part in re.split(r"[^a-zA-Z0-9]+", corpus_name) if part)


def build_retrieval_tools(input_root: Path) -> list[CorpusRetrievalTool]:
    """Build one BM25 retrieval tool per corpus below input_root/retrieval-corpora/.

    Indices are built once per corpus and reused for every case, since indexing
    is expensive relative to searching a handful of queries per case. Each
    corpus gets its own Tool subclass with a corpus-specific name/description,
    so the model sees one distinct tool per corpus (for instance
    retrieve_hessian_law_de) instead of one generic tool with a corpus parameter.

    Progress is reported to stdout per corpus, since indexing a single corpus
    can take from seconds to a few minutes depending on its size.
    """
    corpora = discover_corpora(input_root)
    if not corpora:
        print("No retrieval-corpora found; continuing without retrieval tools.", flush=True)
        return []

    print(f"Building {len(corpora)} retrieval tool(s): {', '.join(corpora)}", flush=True)
    tools = []
    for corpus_index, (corpus_name, documents_path) in enumerate(corpora.items(), start=1):
        started = time.monotonic()
        print(
            f"[{corpus_index}/{len(corpora)}] Building retrieval tool for '{corpus_name}'...",
            flush=True,
        )
        documents = read_documents(documents_path)
        language = infer_language(corpus_name, documents[0])
        index, chunks = build_index(documents, language)
        chunks_by_id = {
            chunk["chunk_id"]: chunk
            for chunk in chunks
        }
        elapsed = time.monotonic() - started
        print(
            f"[{corpus_index}/{len(corpora)}] Indexed {len(chunks)} chunk(s) "
            f"from {len(documents)} document(s) from "
            f"'{corpus_name}' ({language}) in {elapsed:.1f}s.",
            flush=True,
        )

        tool_class = type(
            _tool_class_name(corpus_name),
            (CorpusRetrievalTool,),
            {
                "name": "retrieve_"
                + re.sub(r"[^a-z0-9]+", "_", corpus_name.casefold()).strip("_"),
                "description": (
                    f"Search the '{corpus_name}' retrieval corpus with BM25 and return ranked, "
                    "cited snippets. "
                    f"{CORPUS_DESCRIPTIONS.get(corpus_name, 'Background corpus discovered under retrieval-corpora/.')}"
                ),
                "inputs": {
                    "query": {
                        "type": "string",
                        "description": "Search terms or a short question, in the corpus language.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of ranked hits, between 1 and 20.",
                        "nullable": True,
                    },
                },
            },
        )
        tools.append(tool_class(corpus_name, chunks_by_id, index, language))
        log_tool_calls(tools[-1])

    print(
        f"Finished building all {len(tools)} retrieval tool(s): "
        + ", ".join(tool.name for tool in tools),
        flush=True,
    )
    return tools

