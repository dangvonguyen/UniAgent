#!/usr/bin/env python3

import argparse
import json
import os
from pathlib import Path
from typing import Any

from src.check import check_case, load_case
from src.digest import build_digest
from src.llm import LLM
from src.models import Decision, ResolvedRule, RuleVerdict
from src.retrieval import build_index
from src.rules import RULES
from src.tracelog import Trace

RETRIEVAL_CORPORA_DIR = "retrieval-corpora"


def required_environment() -> tuple[str, str, str]:
    values = []
    for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "OPENAI_MODEL"):
        value = os.environ.get(name, "").strip()
        if not value:
            raise RuntimeError(f"Required environment variable {name} is not set.")
        values.append(value)
    return values[0], values[1], values[2]


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


def _decision_answer(result: str, verdicts: list[RuleVerdict]) -> str:
    if result == "angenommen":
        return "The application satisfies all checked rules."
    reasons = "; ".join(v.reason for v in verdicts if v.verdict == "fail")
    return f"The application is rejected: {reasons}"


def _decision_evidence(verdicts: list[RuleVerdict]) -> list[dict[str, Any]]:
    evidence = []
    for v in verdicts:
        for q in v.case_quotes:
            evidence.append(
                {
                    "source_id": q.document,
                    "quote": q.quote,
                    "relevance": f"{v.rule_id} ({v.verdict}): {v.reason}",
                }
            )
        for q in v.policy_quotes:
            evidence.append(
                {
                    "source_id": f"{q.corpus}/{q.doc_id}",
                    "quote": q.quote,
                    "relevance": f"{v.rule_id}: policy basis",
                }
            )
    return evidence


def decide_case(
    case_dir: Path, rules: list[ResolvedRule], llm: LLM, trace: Trace
) -> dict[str, Any]:
    with trace.case(case_dir.name):
        try:
            case = load_case(case_dir)
        except Exception as err:
            print(f"  ! {case_dir.name}: failed to load case: {err}", flush=True)
            trace.log("error", status="error", error=str(err))
            raise
        trace.log("input", output={"documents": [d.name for d in case.documents]})

        verdicts = check_case(case, rules, llm, trace)
        failed = any(v.verdict == "fail" for v in verdicts)
        decision = Decision(
            case_id=case.case_id,
            result="abgelehnt" if failed else "angenommen",
            verdicts=verdicts,
        )
        trace.log(
            "decision",
            output={
                "decision": decision.result,
                "answer": _decision_answer(decision.result, verdicts),
                "evidence": _decision_evidence(verdicts),
            },
        )
    return {"antrag": case.case_id, "result": decision.result}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-tokens", type=int, default=8192)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    api_base, api_key, model = required_environment()

    input_root = args.input.resolve()
    corpora_root = input_root / RETRIEVAL_CORPORA_DIR
    trace_path = args.output / "run-trace.jsonl.log.gz"
    predictions_path = args.output / "predictions.jsonl"

    with (
        Trace(trace_path, model) as trace,
        predictions_path.open("w", encoding="utf-8") as predictions,
    ):
        # Phase 1: build the retrieval index over the mounted corpora.
        print(f"Building corpus index over {input_root}...", flush=True)
        index = build_index(corpora_root)

        llm = LLM(api_base, api_key, model, args.max_tokens, trace)

        # Phase 2: resolve every rule's policy quotes once, shared across all cases.
        print(f"Resolving policy digest for {len(RULES)} rules...", flush=True)
        with trace.case("-"):
            rules = build_digest(RULES, index, llm, trace)
            for r in rules:
                print(f"  - {r.rule.id}: {len(r.quotes)} policy quote(s)", flush=True)

        # Phase 3: decide each case against the resolved rule digest.
        cases = case_dirs(input_root)
        print(f"Deciding {len(cases)} case(s)...", flush=True)
        for case_dir in cases:
            prediction = decide_case(case_dir, rules, llm, trace)
            predictions.write(json.dumps(prediction, ensure_ascii=False) + "\n")
            print(f"  {case_dir.name}: {prediction['result']}", flush=True)

    print(f"Done. Predictions written to {predictions_path}", flush=True)


if __name__ == "__main__":
    main()
