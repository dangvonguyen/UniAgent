from typing import Any, TypedDict

import pyterrier as pt

from src.config import RESOURCES_DIR


class LanguageConfig(TypedDict):
    stemmer: pt.TerrierStemmer
    stopwords: pt.TerrierStopwords | list[str]
    tokeniser: pt.TerrierTokeniser


LANGUAGE_CONFIG: dict[str, LanguageConfig] = {
    "de": {
        "stemmer": pt.TerrierStemmer.german,
        "stopwords": (RESOURCES_DIR / "german-stopwords.txt").read_text(encoding="utf-8").splitlines(),
        "tokeniser": pt.TerrierTokeniser.utf,
    },
    "en": {
        "stemmer": pt.TerrierStemmer.porter,
        "stopwords": pt.TerrierStopwords.terrier,
        "tokeniser": pt.TerrierTokeniser.english,
    },
}  # fmt: skip


def infer_language(corpus_name: str, sample_document: dict[str, Any]) -> str:
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
