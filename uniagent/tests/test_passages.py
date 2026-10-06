"""Passage splitting tests. All policy text and values are invented (see CLAUDE.md)."""

import re

import pytest

from src.config import PASSAGE_MAX_CHARS, PASSAGE_TAIL_MIN_CHARS, PASSAGE_TARGET_CHARS
from src.retrieval.passages import split_into_passages
from src.text import normalize_text

FILLER = (
    "Die Hochschule informiert ihre Mitglieder regelmäßig über organisatorische "
    "Änderungen in der Verwaltung und bittet um Beachtung der jeweiligen Hinweise. "
)

LAW_STYLE = (
    "§ 7\n\nSonderfahrten\n\n"
    + (FILLER * 6).strip()
    + "\n\n(1) Kosten für Sonderfahrten werden nur erstattet für Fahrten\n\n"
    "1.\n\nmit dem Lastenrad, wenn die Strecke mehr als 17 km beträgt,\n\n"
    "2.\n\nmit dem Ruderboot, sofern kein Steg näher als 3 km liegt.\n\n"
    "(2) " + (FILLER * 8).strip()
)

HEADING_PAGE = (
    (FILLER * 9).strip() + "\n\nAllgemeines zur Ballonfahrt\n\n"
    "• Ballonfahrten über 45 € bedürfen einer schriftlichen Begründung.\n"
    "• Die Begründung ist vor Fahrtantritt einzureichen.\n\n" + (FILLER * 4).strip()
)

RULE_WITH_EXCEPTIONS = (
    (FILLER * 8).strip()
    + "\n\nTaxifahrten über 30 € werden nur erstattet, es sei denn:\n\n"
    "• es lag eine schriftliche Begründung vor, oder\n"
    "• kein öffentliches Verkehrsmittel fuhr nach 23 Uhr.\n\n" + (FILLER * 8).strip()
)

LONG_PARAGRAPH = " ".join(
    f"Nach Nr. {i} gem. § {i} Abs. 2 gilt z. B. für Gruppe {i} eine Frist von {i} Tagen."
    for i in range(1, 300)
)

DOCUMENTS = {
    "law": LAW_STYLE,
    "heading": HEADING_PAGE,
    "exceptions": RULE_WITH_EXCEPTIONS,
    "long": LONG_PARAGRAPH,
    "short": "Kurzer Hinweis.",
}


def split(text: str, language: str = "de"):
    return split_into_passages(
        "corpus-de", "doc-1", "Titel", text, language, normalize=True
    )


def passage_containing(passages, needle: str):
    matches = [p for p in passages if needle in p.text]
    assert len(matches) == 1, f"{needle!r} in {len(matches)} passages"
    return matches[0]


def test_normalize_removes_invisible_characters_and_unifies_spaces():
    raw = "Sta­ke­hol­der Treffen \t  am​ Ort  \n\n\n\n  Zeile zwei \r\n"
    assert normalize_text(raw) == "Stakeholder Treffen am Ort\n\nZeile\nzwei"


@pytest.mark.parametrize("name", DOCUMENTS)
def test_passages_cover_the_document_exactly_once(name):
    passages = split(DOCUMENTS[name])
    body = normalize_text(DOCUMENTS[name])
    assert re.sub(r"\s", "", "".join(p.text for p in passages)) == re.sub(
        r"\s", "", body
    )
    assert [p.index for p in passages] == list(range(len(passages)))
    for previous, current in zip(passages, passages[1:]):
        assert previous.end_char <= current.start_char
    for passage in passages:
        assert passage.text == body[passage.start_char : passage.end_char]
        assert passage.text == passage.text.strip()
        assert "Titel" not in passage.text


@pytest.mark.parametrize("name", DOCUMENTS)
def test_passages_respect_the_maximum_and_have_stable_ids(name):
    passages = split(DOCUMENTS[name])
    assert all(len(p.text) <= PASSAGE_MAX_CHARS for p in passages)
    assert passages == split(DOCUMENTS[name])
    assert [p.passage_id for p in passages] == [
        f"doc-1#{i}" for i in range(len(passages))
    ]


def test_numbered_clause_stays_with_its_lead_in():
    passage = passage_containing(split(LAW_STYLE), "Sonderfahrten werden nur erstattet")
    assert "mit dem Lastenrad, wenn die Strecke mehr als 17 km" in passage.text
    assert "sofern kein Steg näher als 3 km liegt." in passage.text


def test_rule_stays_with_its_exceptions():
    passage = passage_containing(split(RULE_WITH_EXCEPTIONS), "Taxifahrten über 30 €")
    assert "schriftliche Begründung" in passage.text
    assert "nach 23 Uhr" in passage.text


def test_long_paragraph_breaks_at_sentence_ends_not_abbreviations():
    passages = split(LONG_PARAGRAPH)
    assert len(passages) > 1
    for passage in passages:
        assert passage.text.startswith("Nach Nr.")
        assert passage.text.endswith("Tagen.")


def test_small_tail_is_not_left_alone():
    text = "\n\n".join(
        [(FILLER * 7).strip(), (FILLER * 7).strip(), "Ende der Seite hier."]
    )
    passages = split(text)
    assert len(passages[-1].text) >= PASSAGE_TAIL_MIN_CHARS or len(passages) == 1


def test_short_document_is_one_passage():
    assert [p.text for p in split("Kurzer Hinweis.")] == ["Kurzer Hinweis."]
    assert split("  ­ \n\n ") == []


def test_target_is_below_maximum():
    assert PASSAGE_TAIL_MIN_CHARS <= PASSAGE_TARGET_CHARS <= PASSAGE_MAX_CHARS
