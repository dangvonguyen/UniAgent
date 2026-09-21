from typing import Any

from sentence_transformers import SentenceTransformer


MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

RRF_K = 60


class HybridReranker:
    """Fuse lexical candidate ranking with dense semantic ranking."""

    def __init__(
        self,
        model_name: str = MODEL_NAME,
    ) -> None:
        self.model = SentenceTransformer(
            model_name,
            device="cpu",
        )

    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        if not candidates:
            return []

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        texts = [
            candidate.get(
                "text",
                "",
            )
            for candidate in candidates
        ]

        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )[0]

        document_embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            batch_size=16,
            show_progress_bar=False,
        )

        dense_scores = (
            document_embeddings
            @ query_embedding
        )

        enriched: list[
            dict[str, Any]
        ] = []

        # candidates are already ordered by lexical retrieval quality.
        for bm25_rank, (
            candidate,
            dense_score,
        ) in enumerate(
            zip(
                candidates,
                dense_scores,
            ),
            start=1,
        ):
            item = dict(
                candidate
            )

            item["bm25_rank"] = (
                bm25_rank
            )

            item["dense_score"] = (
                float(dense_score)
            )

            enriched.append(
                item
            )

        dense_sorted = sorted(
            enriched,
            key=lambda item: (
                item["dense_score"]
            ),
            reverse=True,
        )

        dense_rank_by_chunk: dict[
            tuple[Any, Any],
            int,
        ] = {}

        for dense_rank, item in enumerate(
            dense_sorted,
            start=1,
        ):
            key = (
                item.get("corpus"),
                item.get("chunk_id")
                or item.get("doc_id"),
            )

            dense_rank_by_chunk[
                key
            ] = dense_rank

        for item in enriched:
            key = (
                item.get("corpus"),
                item.get("chunk_id")
                or item.get("doc_id"),
            )

            dense_rank = (
                dense_rank_by_chunk[
                    key
                ]
            )

            item["dense_rank"] = (
                dense_rank
            )

            item["hybrid_score"] = (
                1.0
                / (
                    RRF_K
                    + item["bm25_rank"]
                )
                + 1.0
                / (
                    RRF_K
                    + dense_rank
                )
            )

        enriched.sort(
            key=lambda item: (
                item["hybrid_score"]
            ),
            reverse=True,
        )

        return enriched[
            :top_k
        ]