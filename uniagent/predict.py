#!/usr/bin/env python3

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from src.check import check_case, load_case
from src.config import DEFAULT_MAX_TOKENS, RETRIEVAL_CORPORA_DIR, Settings
from src.digest import build_digest
from src.llm import LLM
from src.models import Decision, ResolvedRule, RuleVerdict
from src.retrieval import build_index
from src.rules import RULES
from src.tracelog import Trace


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
        for case_q in v.case_quotes:
            evidence.append(
                {
                    "source_id": case_q.document,
                    "quote": case_q.quote,
                    "relevance": f"{v.rule_id} ({v.verdict}): {v.reason}",
                }
            )
        for policy_q in v.policy_quotes:
            evidence.append(
                {
                    "source_id": f"{policy_q.corpus}/{policy_q.doc_id}",
                    "quote": policy_q.quote,
                    "relevance": f"{v.rule_id}: policy basis",
                }
            )
    return evidence


async def decide_case(
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

        verdicts = await check_case(case, rules, llm, trace)
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


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    settings = Settings.from_env()

    input_root = args.input.resolve()
    corpora_root = input_root / RETRIEVAL_CORPORA_DIR
    trace_path = args.output / "run-trace.jsonl.log.gz"
    predictions_path = args.output / "predictions.jsonl"

    with (
        Trace(trace_path, settings.openai_model) as trace,
        predictions_path.open("w", encoding="utf-8") as predictions,
    ):
        # Phase 1: build the retrieval index over the mounted corpora.
        index = await build_index(corpora_root)

        llm = LLM(
            settings.openai_base_url,
            settings.openai_api_key,
            settings.openai_model,
            args.max_tokens,
            trace,
        )

        # Phase 2: resolve every rule's policy quotes once, shared across all cases.
        # Each rule traces under its own case_id.
        rules = await build_digest(RULES, index, llm, trace)

        # Phase 3: decide each case against the resolved rule digest, concurrently.
        cases = case_dirs(input_root)
        print(f"Deciding {len(cases)} case(s)...", flush=True)

        async def _decide_indexed(i: int, case_dir: Path) -> tuple[int, dict[str, Any]]:
            return i, await decide_case(case_dir, rules, llm, trace)

        tasks = [
            asyncio.create_task(_decide_indexed(i, case_dir))
            for i, case_dir in enumerate(cases)
        ]
        results: list[dict[str, Any] | None] = [None] * len(cases)
        try:
            for coro in asyncio.as_completed(tasks):
                i, prediction = await coro
                results[i] = prediction
                print(f"  {cases[i].name}: {prediction['result']}", flush=True)
        except BaseException:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise
        for result in results:
            assert result is not None
            predictions.write(json.dumps(result, ensure_ascii=False) + "\n")

    print(f"Done. Predictions written to {predictions_path}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
