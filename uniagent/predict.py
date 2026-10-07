#!/usr/bin/env python3

import argparse
import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

from src.check import check_case, load_case
from src.config import DEFAULT_MAX_TOKENS, RETRIEVAL_CORPORA_DIR, Settings
from src.digest import build_digest
from src.llm import LLM
from src.models import Decision, ResolvedRule, RuleVerdict
from src.policy_cache import load as load_policy_cache, save as save_policy_cache
from src.policy_cache import signature as policy_signature
from src.reflect import reflect_case
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
        unknown = [v.rule_id for v in verdicts if v.verdict == "unknown"]
        if unknown:
            return ("No failure among decided rules; unresolved technical/rule findings: "
                    + ", ".join(unknown))
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
        started = time.monotonic()
        try:
            async with asyncio.timeout(295):
                case = load_case(case_dir)
                trace.log("input", output={"documents": [d.name for d in case.documents]})
                verdicts = await check_case(case, rules, llm, trace)
                if verdicts and all(v.verdict == "unknown" for v in verdicts):
                    raise RuntimeError(
                        "All first-pass rules are unknown; refusing an accepted label "
                        "without any evaluated rule"
                    )
                candidate_result = ("abgelehnt" if any(v.verdict == "fail" for v in verdicts)
                                    else "angenommen")
                mode = os.environ.get("UNIAGENT_REFLECT_MODE", "shadow").strip().lower()
                if mode not in {"shadow", "commit", "off"}:
                    raise ValueError("UNIAGENT_REFLECT_MODE must be shadow, commit or off")
                review = await reflect_case(
                    case, rules, verdicts, llm, trace, mode=mode,
                    timeout_seconds=min(80, max(0, 290 - (time.monotonic() - started))),
                )
        except Exception as err:
            print(f"  ! {case_dir.name}: case failed or exceeded 300s: {err}", flush=True)
            trace.log("error", status="error", error=str(err))
            raise

        verdicts = review.final_verdicts
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
                "candidate_decision": candidate_result,
                "proposed_decision": "abgelehnt" if any(
                    v.verdict == "fail" for v in review.proposed_verdicts
                ) else "angenommen",
                "reflect_mode": review.mode,
                "reviewed_rule_ids": review.reviewed_rule_ids,
                "review_changes": review.changes,
                "review_issues": review.issues,
                "unknown_rules": [v.rule_id for v in verdicts if v.verdict == "unknown"],
                "verdicts": [v.model_dump() for v in verdicts],
                "elapsed_seconds": round(time.monotonic() - started, 3),
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
    parser.add_argument("--policy-cache", type=Path,
                        help="Persist and reuse an exact policy digest snapshot")
    parser.add_argument("--refresh-policy-cache", action="store_true",
                        help="Explicitly rebuild a stale or existing policy snapshot")
    parser.add_argument("--prepare-policy-only", action="store_true",
                        help="Prepare the digest and exit before processing cases")
    args = parser.parse_args()
    if (args.refresh_policy_cache or args.prepare_policy_only) and not args.policy_cache:
        parser.error("--refresh-policy-cache and --prepare-policy-only require --policy-cache")
    args.output.mkdir(parents=True, exist_ok=True)

    settings = Settings.from_env()

    input_root = args.input.resolve()
    corpora_root = input_root / RETRIEVAL_CORPORA_DIR
    trace_path = args.output / "run-trace.jsonl.log.gz"
    predictions_path = args.output / "predictions.jsonl"

    with Trace(trace_path, settings.openai_model) as trace:
        llm = LLM(
            settings.openai_base_url,
            settings.openai_api_key,
            settings.openai_model,
            args.max_tokens,
            trace,
        )

        # A cache hit skips index construction and all digest model calls.
        key = (policy_signature(corpora_root, RULES, settings.openai_model,
                                settings.openai_base_url, args.max_tokens)
               if args.policy_cache else None)
        if args.policy_cache and args.policy_cache.exists() and not args.refresh_policy_cache:
            rules = load_policy_cache(args.policy_cache, key, RULES)
            origin = "loaded"
        else:
            index = await build_index(corpora_root)
            rules = await build_digest(RULES, index, llm, trace)
            origin = "rebuilt"
            if not any(resolved.quotes for resolved in rules):
                raise RuntimeError("Policy digest returned no quotes for any rule; "
                                   "refusing to cache an empty digest")
            if args.policy_cache:
                save_policy_cache(args.policy_cache, key, rules)
        trace.log("policy_cache", output={
            "state": origin, "signature": key,
            "quote_counts": {r.rule.id: len(r.quotes) for r in rules},
            "missing_rules": [r.rule.id for r in rules if not r.quotes],
        })
        print(f"Policy digest {origin}; missing quote(s) for: "
              f"{[r.rule.id for r in rules if not r.quotes]}", flush=True)
        if not any(resolved.quotes for resolved in rules):
            raise RuntimeError("Policy digest returned no quotes for any rule; no case verdicts are valid")
        if args.prepare_policy_only:
            print(f"Policy digest prepared: {args.policy_cache}", flush=True)
            return

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
        with predictions_path.open("w", encoding="utf-8") as predictions:
            for result in results:
                assert result is not None
                predictions.write(json.dumps(result, ensure_ascii=False) + "\n")

    print(f"Done. Predictions written to {predictions_path}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
