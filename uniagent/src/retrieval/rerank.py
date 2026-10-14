"""GTE cross-encoder reranking of the top BM25 candidate chunks."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import numpy as np

from src.config import (
    GTE_BATCH_SIZE,
    GTE_CODE_REVISION,
    GTE_MAX_LENGTH,
    GTE_MODEL,
    GTE_MODEL_REVISION,
    GTE_RERANK_DEPTH,
)

from .fusion import FusedHit


def load_gte_model(max_length: int = GTE_MAX_LENGTH) -> Any:
    """Load the pinned CPU GTE reranker, respecting Hugging Face offline mode."""
    import torch
    from huggingface_hub import snapshot_download
    from sentence_transformers import CrossEncoder

    offline = os.environ.get("HF_HUB_OFFLINE", "").lower() in {"1", "true", "yes"}
    model_path = snapshot_download(
        GTE_MODEL,
        revision=GTE_MODEL_REVISION,
        local_files_only=offline,
    )
    revision_kwargs = {"code_revision": GTE_CODE_REVISION}
    return CrossEncoder(
        model_path,
        trust_remote_code=True,
        device="cpu",
        backend="torch",
        max_length=max_length,
        model_kwargs={"dtype": torch.float32, **revision_kwargs},
        config_kwargs=revision_kwargs,
    )


class GteReranker:
    """Rerank at most ``depth`` sparse chunks with natural-language questions."""

    def __init__(
        self,
        model: Any,
        *,
        depth: int = GTE_RERANK_DEPTH,
        batch_size: int = GTE_BATCH_SIZE,
    ) -> None:
        if depth < 1 or batch_size < 1:
            raise ValueError("GTE depth and batch size must be positive")
        self._model = model
        self._depth = depth
        self._batch_size = batch_size

    def rerank(
        self,
        sparse_hits: list[FusedHit],
        questions: dict[str, list[str]],
        language_for_corpus: Callable[[str], str],
    ) -> list[FusedHit]:
        """Score top sparse chunks and use the best question score per chunk."""
        selected = sparse_hits[: self._depth]
        if not selected:
            return []

        fallback_questions = [
            question.strip()
            for language_questions in questions.values()
            for question in language_questions
            if question.strip()
        ]
        if not fallback_questions:
            raise ValueError("GTE reranking requires at least one non-empty question")

        pairs: list[tuple[str, str]] = []
        owners: list[int] = []
        for hit_index, hit in enumerate(selected):
            language = language_for_corpus(hit.passage.corpus)
            candidate_questions = [
                question.strip()
                for question in questions.get(language, [])
                if question.strip()
            ] or fallback_questions
            passage_text = f"{hit.passage.title}\n{hit.passage.text}"
            for question in candidate_questions:
                pairs.append((question, passage_text))
                owners.append(hit_index)

        scores = np.asarray(
            self._model.predict(
                pairs,
                batch_size=self._batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
            ),
            dtype=np.float32,
        ).reshape(-1)
        if scores.shape != (len(pairs),):
            raise RuntimeError(
                f"GTE returned {scores.shape} for {len(pairs)} question/chunk pairs"
            )
        if not np.isfinite(scores).all():
            raise RuntimeError("GTE returned a non-finite score")

        best_scores = np.full(len(selected), -np.inf, dtype=np.float32)
        for owner, score in zip(owners, scores, strict=True):
            best_scores[owner] = max(best_scores[owner], score)

        # The sparse position is the deterministic tie-breaker.
        order = sorted(range(len(selected)), key=lambda i: (-best_scores[i], i))
        return [
            FusedHit(passage=selected[i].passage, score=float(best_scores[i]))
            for i in order
        ]
