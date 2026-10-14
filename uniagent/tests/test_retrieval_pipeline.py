import numpy as np

from src.retrieval.fusion import FusedHit, weighted_fuse_by_reciprocal_rank
from src.retrieval.passages import Passage
from src.retrieval.rerank import GteReranker


def _hit(index: int, score: float = 0.0) -> FusedHit:
    return FusedHit(
        passage=Passage(
            corpus="policy-de",
            doc_id=f"doc-{index}",
            index=0,
            start_char=0,
            end_char=10,
            title=f"Title {index}",
            text=f"Passage {index}",
        ),
        score=score,
    )


def test_weighted_rrf_prefers_the_heavier_gte_ranking() -> None:
    sparse = [_hit(0), _hit(1)]
    gte = [sparse[1], sparse[0]]

    result = weighted_fuse_by_reciprocal_rank(
        ((sparse, 0.3), (gte, 0.7)), rrf_k=60
    )

    assert result[0].passage.doc_id == "doc-1"


class _FakeGte:
    def __init__(self) -> None:
        self.pairs: list[tuple[str, str]] = []

    def predict(self, pairs, **_):
        self.pairs = list(pairs)
        return np.asarray([0.1, 0.9, 0.8, 0.2], dtype=np.float32)


def test_gte_reranks_only_the_configured_depth_and_maxes_questions() -> None:
    model = _FakeGte()
    sparse = [_hit(0), _hit(1), _hit(2)]
    reranked = GteReranker(model, depth=2, batch_size=4).rerank(
        sparse,
        {"de": ["question one", "question two"]},
        lambda _: "de",
    )

    assert len(model.pairs) == 4
    assert [hit.passage.doc_id for hit in reranked] == ["doc-0", "doc-1"]
    assert all("doc-2" not in passage for _, passage in model.pairs)
