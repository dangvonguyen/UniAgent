#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from typing import Any

from src.check import check_case, load_case
from src.digest import build_digest
from src.llm import LLM
from src.models import Decision, ResolvedRule
from src.retrieval import build_index
from src.rules import RULES

RETRIEVAL_CORPORA_DIR = "retrieval-corpora"


def case_dirs(input_dir: Path) -> list[Path]:
    if not input_dir.is_dir():
        raise ValueError(f"Input directory does not exist: {input_dir}")
    cases = sorted(
        path
        for path in input_dir.iterdir()
        if path.is_dir()
        and path.name != RETRIEVAL_CORPORA_DIR
        and any(path.glob("*.pdf"))
    )
    if not cases:
        raise ValueError(f"No application directories found in {input_dir}")
    return cases


def decide_case(case_dir: Path, rules: list[ResolvedRule], llm: LLM) -> dict[str, Any]:
    case = load_case(case_dir)
    verdicts = check_case(case, rules, llm)
    failed = any(v.verdict == "fail" for v in verdicts)
    decision = Decision(
        case_id=case.case_id,
        result="abgelehnt" if failed else "angenommen",
        verdicts=verdicts,
    )
    return {"antrag": case.case_id, "result": decision.result}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-tokens", type=int, default=8192)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    llm = LLM(args.max_tokens)
    index = build_index(args.input / RETRIEVAL_CORPORA_DIR)
    rules = build_digest(RULES, index, llm)

    with (args.output / "predictions.jsonl").open("w", encoding="utf-8") as predictions:
        for case_dir in case_dirs(args.input):
            prediction = decide_case(case_dir, rules, llm)
            predictions.write(json.dumps(prediction, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
