"""Gold for retrieval evaluation: the verbatim policy quotes each rule needs the LLM to see."""

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_GOLD_PATH = Path(__file__).parent / "gold.json"


@dataclass(frozen=True)
class GoldQuote:
    key: str
    corpus: str
    doc_id: str
    quote: str


Gold = dict[str, list[GoldQuote]]  # rule id -> quotes the rule needs


def load_gold(path: Path = DEFAULT_GOLD_PATH) -> Gold:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        rule_id: [GoldQuote(**item) for item in items]
        for rule_id, items in raw["rules"].items()
    }
