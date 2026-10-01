"""Centralized runtime configuration: environment-derived settings and tunable constants."""

import os
from pathlib import Path

from pydantic import BaseModel

REQUIRED_ENV_VARS = ("OPENAI_BASE_URL", "OPENAI_API_KEY", "OPENAI_MODEL")

RETRIEVAL_CORPORA_DIR = "retrieval-corpora"
DEFAULT_MAX_TOKENS = 8192

WORK_DIR = Path(__file__).resolve().parents[1]

RESOURCES_DIR = WORK_DIR / "resources"

# caches
CACHE_DIR = WORK_DIR / "runs"
PASSAGE_CACHE_DIR = CACHE_DIR / "passages"
INDEX_CACHE_DIR = CACHE_DIR / "indices"
EMBEDDING_CACHE_DIR = CACHE_DIR / "embeddings"

# llm
LLM_MAX_RETRIES = 2
LLM_TIMEOUT_SECONDS = 120
LLM_COMPLETION_ATTEMPTS = 2
LLM_TEMPERATURE = 0
LLM_MAX_CONCURRENCY = 8

# digest
DIGEST_CONTEXT_K = 10  # excerpts handed to the LLM when resolving one rule
DIGEST_MAX_DOC_CHARS = 3000

# retrieval
RETRIEVAL_DOCNO_META_LENGTH = 100
RETRIEVAL_DEPTH = 100  # hits per (query, corpus) pair, before fusion
RETRIEVAL_RRF_K = 60
RETRIEVAL_WMODEL = "BM25"

# dense
DENSE_MODEL = "sentence-transformers/static-similarity-mrl-multilingual-v1"
DENSE_BATCH_SIZE = 256

# passages
PASSAGE_TARGET_CHARS = 1500
PASSAGE_MAX_CHARS = 2500
PASSAGE_MIN_STANDALONE_BLOCK_CHARS = 100
PASSAGE_TAIL_MIN_CHARS = PASSAGE_TARGET_CHARS // 2


class Settings(BaseModel):
    openai_base_url: str
    openai_api_key: str
    openai_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        values: dict[str, str] = {}
        for name in REQUIRED_ENV_VARS:
            value = os.environ.get(name, "").strip()
            if not value:
                raise RuntimeError(f"Required environment variable {name} is not set.")
            values[name] = value
        return cls(
            openai_base_url=values["OPENAI_BASE_URL"],
            openai_api_key=values["OPENAI_API_KEY"],
            openai_model=values["OPENAI_MODEL"],
        )
