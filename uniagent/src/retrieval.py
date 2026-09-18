from __future__ import annotations

import gzip
import json
import tempfile
from pathlib import Path
from typing import Any

import pyterrier as pt

LANGUAGE_CONFIG = {
    "de": {
        "stemmer": pt.TerrierStemmer.german,
        "stopwords": (Path(__file__).parent.parent / "resources" / "german-stopwords.txt").read_text(encoding="utf-8").splitlines(),
        "tokeniser": pt.TerrierTokeniser.utf,
    },
    "en": {
        "stemmer": pt.TerrierStemmer.porter,
        "stopwords": pt.TerrierStopwords.terrier,
        "tokeniser": pt.TerrierTokeniser.english,
    },
}  # fmt: skip

DOCNO_META_LENGTH = 100

Document = dict[str, Any]
CorpusDocuments = tuple[list[Document], str]  # (documents, language) for one corpus


class CorpusRetriever:
    def __init__(
        self, corpus_name: str, documents: list[Document], language: str
    ) -> None:
        if language not in LANGUAGE_CONFIG:
            raise ValueError(f"Unsupported corpus language: {language}")
        if not documents:
            raise ValueError(f"Corpus {corpus_name!r} contains no documents.")

        self._corpus_name = corpus_name
        self._language = language

        self._index_dir = Path(tempfile.mkdtemp(prefix=f"index-{corpus_name}_"))
        self._texts = {str(doc["doc_id"]): doc.get("text") or "" for doc in documents}
        self._index = self._build_index(documents)

    def search(
        self, query: str, *, num_results: int = 5, wmodel: str = "BM25"
    ) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            raise ValueError("Query must not be empty.")
        if not 1 <= num_results <= 1000:
            raise ValueError("num_results must be between 1 and 1000.")

        retriever = self._index.retriever(wmodel, num_results=num_results)
        results = retriever.search(query)
        return [
            {
                "docno": row.docno,
                "rank": int(row.rank),
                "score": float(row.score),
                "corpus": self._corpus_name,
                "text": self._texts.get(row.docno, ""),
            }
            for row in results.itertuples()
        ]

    def _build_index(self, documents: list[Document]) -> pt.terrier.TerrierIndex:
        index = pt.terrier.TerrierIndex(str(self._index_dir))
        indexer = index.indexer(
            meta={"docno": DOCNO_META_LENGTH},
            **LANGUAGE_CONFIG[self._language],
        )
        indexer.index(
            {"docno": str(doc["doc_id"]), "text": doc.get("text") or ""}
            for doc in documents
        )
        return index


class CorpusIndex:
    def __init__(self, retrievers: dict[str, CorpusRetriever]) -> None:
        self._retrievers = retrievers

    @classmethod
    def build(cls, corpus_documents: dict[str, CorpusDocuments]) -> CorpusIndex:
        return cls(
            {
                corpus_name: CorpusRetriever(corpus_name, documents, language)
                for corpus_name, (documents, language) in corpus_documents.items()
                if documents
            }
        )

    @property
    def corpora(self) -> list[str]:
        return list(self._retrievers)

    def search(
        self,
        query: str,
        num_results: int = 10,
        wmodel: str = "BM25",
        corpora: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            raise ValueError("Query must not be empty.")
        if not 1 <= num_results <= 1000:
            raise ValueError("num_results must be between 1 and 1000.")

        targets = corpora if corpora else self.corpora
        hits = []
        for corpus_name in targets:
            retriever = self._retrievers.get(corpus_name)
            if retriever is None:
                continue
            hits.extend(retriever.search(query, num_results=num_results, wmodel=wmodel))
        hits.sort(key=lambda hit: hit["score"], reverse=True)
        # TODO: score are different between corpus
        return hits[:num_results]


def load_corpora(corpora_root: Path) -> dict[str, Path]:
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


def infer_language(corpus_name: str, sample_document: Document) -> str:
    if corpus_name.endswith("-de"):
        return "de"
    if corpus_name.endswith("-en"):
        return "en"
    language = str(sample_document.get("language", "")).strip().casefold()
    if language in LANGUAGE_CONFIG:
        return language
    raise ValueError(
        f"Cannot infer a supported language for corpus {corpus_name!r}; "
        "expected a '-de'/'-en' folder suffix or a 'language' document field."
    )


def load_documents(corpora_root: Path) -> dict[str, CorpusDocuments]:
    corpus_documents: dict[str, CorpusDocuments] = {}
    for corpus_name, documents_path in load_corpora(corpora_root).items():
        documents = read_documents(documents_path)
        language = infer_language(corpus_name, documents[0])
        corpus_documents[corpus_name] = (documents, language)
    return corpus_documents


def build_index(corpora_root: Path) -> CorpusIndex:
    return CorpusIndex.build(load_documents(corpora_root))
