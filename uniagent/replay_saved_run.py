#!/usr/bin/env python3
"""Replay check and Reflect code on recorded model responses, without network calls."""

from __future__ import annotations

import argparse
import asyncio
import gzip
import hashlib
import json
import os
from pathlib import Path

from predict import decide_case
from src.models import PolicyQuote, ResolvedRule
from src.rules import RULES
from src.tracelog import Trace


class ReplayMismatch(BaseException):
    """Stop the replay even though production code catches model exceptions."""


class RecordedLLM:
    def __init__(self, calls: dict[str, list[dict]]):
        self.calls = calls
        self.reused = 0

    async def complete_json(self, system, user, schema, *, context=""):
        attempts = self.calls.get(context, [])
        if not attempts:
            raise ReplayMismatch(f"No recorded response for {context}")
        expected_user = user + "\n\nJSON schema of the answer:\n" + json.dumps(
            schema.model_json_schema(), ensure_ascii=False)
        for entry in attempts:
            messages = (entry.get("input") or {}).get("messages", [])
            if (len(messages) != 2 or messages[0].get("content") != system
                or messages[1].get("content") != expected_user):
                raise ReplayMismatch(f"Recorded model input differs for {context}; "
                                     "a prompt or source changed, so replay is invalid")
        self.reused += 1
        for entry in reversed(attempts):
            content = (entry.get("output") or {}).get("content")
            if isinstance(content, dict):
                return schema.model_validate(content)
        # The original transport returns an empty schema after exhausted retries.
        return schema()


class RecordingTrace:
    def __init__(self, trace: Trace):
        self.trace = trace
        self.decisions: dict[str, dict] = {}
        self.case_id = "-"

    def case(self, case_id):
        from contextlib import contextmanager

        @contextmanager
        def scope():
            old = self.case_id
            self.case_id = case_id
            try:
                with self.trace.case(case_id):
                    yield
            finally:
                self.case_id = old
        return scope()

    def log(self, kind, **kwargs):
        if kind == "decision":
            self.decisions[self.case_id] = kwargs["output"]
        return self.trace.log(kind, **kwargs)


def _read_source(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        events = [json.loads(line) for line in stream]
    calls: dict[str, list[dict]] = {}
    quotes: dict[str, dict[str, list[dict]]] = {}
    original: dict[str, dict] = {}
    for event in events:
        case_id, kind = event.get("case_id"), event.get("event_type")
        if kind == "model_call":
            context = (event.get("input") or {}).get("context")
            if context and (":check_rule:" in context or ":reflect:" in context):
                calls.setdefault(context, []).append(event)
        elif kind == "observation" and isinstance(event.get("output"), dict):
            output = event["output"]
            if case_id and ("rule_id" in output and "policy_quotes" in output):
                quotes.setdefault(case_id, {})[output["rule_id"]] = output["policy_quotes"]
        elif kind == "decision":
            original[case_id] = event["output"]
    if not original:
        raise ValueError("Source trace has no completed case decisions")
    return calls, quotes, original


async def replay(args) -> None:
    calls, quotes, original = _read_source(args.trace)
    llm = RecordedLLM(calls)
    args.output.mkdir(parents=True, exist_ok=True)
    trace_path = args.output / "replay-trace.jsonl.log.gz"
    reports = []
    with Trace(trace_path, "replay-recorded-output") as raw_trace:
        trace = RecordingTrace(raw_trace)
        for case_id in sorted(original):
            case_dir = args.input / case_id
            if not case_dir.is_dir():
                raise ValueError(f"Case PDFs missing: {case_dir}")
            case_quotes = quotes.get(case_id, {})
            if set(case_quotes) != {rule.id for rule in RULES}:
                raise ValueError(f"Policy observations incomplete for {case_id}")
            rules = [ResolvedRule(rule=rule,
                                  quotes=[PolicyQuote.model_validate(q)
                                          for q in case_quotes[rule.id]])
                     for rule in RULES]
            snapshot = hashlib.sha256(json.dumps(case_quotes, sort_keys=True,
                ensure_ascii=False).encode("utf-8")).hexdigest()
            os.environ["UNIAGENT_REFLECT_MODE"] = args.reflect_mode
            current = await decide_case(case_dir, rules, llm, trace)
            before = original[case_id]
            now = trace.decisions[case_id]
            old_rules = {v["rule_id"]: v["verdict"] for v in before["verdicts"]}
            new_rules = {v["rule_id"]: v["verdict"] for v in now["verdicts"]}
            changed = {rule_id: {"before": old_rules[rule_id], "after": verdict}
                       for rule_id, verdict in new_rules.items()
                       if verdict != old_rules[rule_id]}
            reports.append({"case_id": case_id, "source_result": before["decision"],
                            "replayed_result": current["result"],
                            "source_proposal": before.get("proposed_decision"),
                            "replayed_proposal": now.get("proposed_decision"),
                            "policy_snapshot_sha256": snapshot,
                            "changed_rules": changed,
                            "replayed_review_issues": now.get("review_issues", [])})
            print(case_id, before["decision"], "->", current["result"], changed,
                  flush=True)
    report = {"source_trace": str(args.trace), "model_calls_reused": llm.reused,
              "reflect_mode": args.reflect_mode, "cases": reports}
    if args.truth:
        truth = {row["antrag"]: row["result"] for line in
                 args.truth.open(encoding="utf-8") if (row := json.loads(line))}
        report["correct"] = sum(row["replayed_result"] == truth[row["case_id"]]
                                for row in reports)
        report["total"] = len(reports)
        print(f"Replay {args.reflect_mode}: {report['correct']}/{report['total']}")
    (args.output / "replay-summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Offline replay summary:", args.output / "replay-summary.json")
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reflect-mode", choices=("shadow", "commit"), default="shadow")
    parser.add_argument("--truth", type=Path)
    asyncio.run(replay(parser.parse_args()))
