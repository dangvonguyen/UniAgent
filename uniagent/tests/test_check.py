from src.check import _resolve_document
from src.models import CaseDocument

DOCS = {
    "C1": CaseDocument(name="antrag.pdf", text="a"),
    "C2": CaseDocument(name="Rechnung.pdf", text="b"),
}


def test_resolves_label_and_filename():
    assert _resolve_document("C2", DOCS) is DOCS["C2"]
    assert _resolve_document("c1", DOCS) is DOCS["C1"]
    assert _resolve_document("rechnung.pdf", DOCS) is DOCS["C2"]


def test_unknown_reference_is_none():
    assert _resolve_document("C9", DOCS) is None
    assert _resolve_document("other.pdf", DOCS) is None
