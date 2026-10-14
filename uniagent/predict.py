#!/usr/bin/env python3

import argparse
import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

from src.check import check_case, load_case
from src.config import CASE_DEADLINE_SECONDS, DEFAULT_MAX_TOKENS, RETRIEVAL_CORPORA_DIR, Settings
from src.digest import build_digest
from src.policy_digest_cache import corpus_signature
from src.llm import LLM
from src.models import Decision, ResolvedRule, RuleVerdict
from src.procurement_decision import procurement_audit_verdicts
from src.procurement_scope_context import retain_retrieved_scope
from src.retrieval import build_index
from src.rules import RULES, TOPICS, CaseType, case_type_for
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
        if any(v.verdict == "unknown" for v in verdicts):
            return "No verified rejection; provisional label with unresolved checks."
        return "No verified rejection under the checked rules."
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
    case_dir: Path, rules: list[ResolvedRule], topic: str, llm: LLM, trace: Trace,
    deadline: float | None = None,
) -> dict[str, Any]:
    case_started = time.monotonic()
    with trace.case(case_dir.name):
        try:
            case = load_case(case_dir)
        except Exception as err:
            print(f"  ! {case_dir.name}: failed to load case: {err}", flush=True)
            trace.log("error", status="error", error=str(err))
            raise
        trace.log("input", output={"documents": [d.name for d in case.documents]})

        audit: list[RuleVerdict] = []
        if case_type_for(case.case_id) == "procurement":
            audit = procurement_audit_verdicts(
                case_dir, rules, trace, {d.name: d.text for d in case.documents})
        if deadline is None:
            verdicts = await check_case(case, rules, topic, llm, trace)
        else:
            # All rule tasks receive the same remaining case budget. Completed
            # rules survive a timeout; unfinished ones become technical gaps.
            tasks = [asyncio.create_task(check_case(case, [r], topic, llm, trace))
                     for r in rules]
            remaining = max(0, deadline - time.monotonic())
            done, pending = await asyncio.wait(tasks, timeout=remaining)
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            verdicts = []
            for rule, task in zip(rules, tasks, strict=True):
                if task in pending:
                    reason = "rule_error: case_deadline_exceeded"
                    verdicts.append(RuleVerdict(rule_id=rule.rule.id,
                                                verdict="unknown", reason=reason))
                else:
                    try:
                        verdicts.append(task.result()[0])
                    except Exception as exc:
                        verdicts.append(RuleVerdict(rule_id=rule.rule.id,
                            verdict="unknown", reason=f"rule_error: {type(exc).__name__}: {exc}"))
        rule_results = [v.model_dump(mode="json") for v in verdicts]
        verdicts.extend(audit)
        failed = any(v.verdict == "fail" for v in verdicts)
        unresolved = [v.rule_id for v in verdicts if v.verdict == "unknown"]
        if unresolved and not failed:
            # Fallback label, not a business verdict: keep it visible in the trace.
            trace.log("observation", tool="decision_fallback", output={
                "label": "angenommen", "unresolved_rules": unresolved,
                "reasons": {v.rule_id: v.reason for v in verdicts if v.verdict == "unknown"},
            })
        decision = Decision(
            case_id=case.case_id,
            result="abgelehnt" if failed else "angenommen",
            verdicts=verdicts,
        )
        trace.log(
            "decision",
            output={
                "decision": decision.result,
                "degraded": bool(unresolved),
                "case_elapsed_seconds": round(time.monotonic() - case_started, 3),
                "technical_rule_gaps": unresolved,
                "rule_results": rule_results,
                "audit_results": [v.model_dump(mode="json") for v in audit],
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
        cases = case_dirs(input_root)
        case_types = list({case_type_for(case_dir.name) for case_dir in cases})

        # Phase 1: build the retrieval index over the mounted corpora.
        signature = await asyncio.to_thread(corpus_signature, corpora_root)
        index = await build_index(corpora_root)

        llm = LLM(
            settings.openai_base_url,
            settings.openai_api_key,
            settings.openai_model,
            args.max_tokens,
            trace,
        )

        # Phase 2: resolve the policy quotes of every rule of the domains, shared across
        # all cases. Each rule traces under its own case_id.
        resolved = await asyncio.gather(
            *(
                build_digest(RULES[case_type], TOPICS[case_type], index, llm, trace,
                             cache_signature=signature, model_name=settings.openai_model,
                             require_warm=os.getenv("UNIAGENT_REQUIRE_WARM") == "1")
                for case_type in case_types
            )
        )
        rules: dict[CaseType, list[ResolvedRule]] = dict(zip(case_types, resolved))
        if 'procurement' in rules:
            await retain_retrieved_scope(rules['procurement'], index, trace)

        # Phase 3: decide each case against its domain's resolved rules, concurrently.
        print(f"Deciding {len(cases)} case(s)...", flush=True)

        # Leave time for cancelled requests, trace flushing and the prediction
        # write. The entire decision, including that overhead, must fit 300 s.
        # Shared corpus preparation is reported separately in the warm-cache step.
        for case_dir in cases:
            case_started = time.monotonic()
            case_type = case_type_for(case_dir.name)
            prediction = await decide_case(
                case_dir, rules[case_type], TOPICS[case_type], llm, trace,
                case_started + max(0, CASE_DEADLINE_SECONDS - 15),
            )
            predictions.write(json.dumps(prediction, ensure_ascii=False) + "\n")
            predictions.flush()
            print(f"  {case_dir.name}: {prediction['result']} "
                  f"({time.monotonic() - case_started:.1f}s)", flush=True)

    print(f"Done. Predictions written to {predictions_path}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
