"""Evaluate retrieval for the policy digest.

    cd uniagent && python -m eval [--label baseline]

Results are written to runs/eval/<label>.json so variants can be compared.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from src import config
from src.models import Rule
from src.retrieval import CorpusIndex, FusedHit
from src.retrieval.corpora import find_corpora, prepare_corpora
from src.rules import RULES

from .coverage import equivalent_doc_ids, evaluate_coverage
from .gold import DEFAULT_GOLD_PATH, load_gold

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS_ROOT = REPO_ROOT / "data/datasets"
DEFAULT_CORPORA = DATASETS_ROOT / "business-trip-spot-check/inputs/retrieval-corpora"
CONFIG_KEYS = (
    "RETRIEVAL_DEPTH",
    "RETRIEVAL_RRF_K",
    "RETRIEVAL_WMODEL",
    "DENSE_MODEL",
    "DIGEST_CONTEXT_K",
    "DIGEST_MAX_DOC_CHARS",
    "PASSAGE_TARGET_CHARS",
    "PASSAGE_MAX_CHARS",
)


def _print_coverage(report: dict) -> None:
    k = report["k"]
    print(
        f"\nPolicy coverage (top {k}, excerpts truncated to {report['max_chars']} chars)"
    )
    print(f"  {'rule':<42} {'cov@' + str(k):>7} {'rec@50':>7} {'rec@100':>8}  missing")
    for rule in report["rules"]:
        if rule["status"] == "no_gold":
            print(f"  {rule['rule_id']:<42} {'-':>7} {'-':>7} {'-':>8}  (no gold)")
            continue
        missing = [
            f"{q['key']}("
            + (f"rank {q['passage_rank']}" if q["passage_rank"] else "not found")
            + ")"
            for q in rule["quotes"]
            if q["passage_rank"] is None or q["passage_rank"] > k
        ]
        print(
            f"  {rule['rule_id']:<42} {rule[f'coverage@{k}']:>7.2f} {rule['recall@50']:>7.2f} "
            f"{rule['recall@100']:>8.2f}  {', '.join(missing)}"
        )
    s = report["summary"]
    print(
        f"  overall coverage@{k} {s[f'coverage@{k}']:.2f}, recall@50 {s['recall@50']:.2f}, "
        f"recall@100 {s['recall@100']:.2f}; rules meeting the bar "
        f"{s['rules_meeting_bar']}/{s['rules_measured']}"
    )
    if s["quotes_split_by_passages"]:
        print(
            f"  quotes no single passage holds whole: {s['quotes_split_by_passages']}"
        )


async def run(args: argparse.Namespace) -> int:
    gold = load_gold(args.gold)
    corpora_paths = find_corpora(args.corpora)
    prepared = await prepare_corpora(args.corpora)
    index = await CorpusIndex.build(prepared)

    async def search(rule: Rule) -> list[FusedHit]:
        return await index.search(
            rule.queries, rule.questions, depth=config.RETRIEVAL_DEPTH
        )

    coverage = await evaluate_coverage(
        RULES, gold, search, prepared, equivalent_doc_ids(corpora_paths, gold)
    )
    _print_coverage(coverage)

    args.out.mkdir(parents=True, exist_ok=True)
    out_path = args.out / f"{args.label}.json"
    out_path.write_text(
        json.dumps(
            {
                "label": args.label,
                "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "config": {key: getattr(config, key) for key in CONFIG_KEYS},
                "coverage": coverage,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"\nWrote {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m eval", description=__doc__)
    parser.add_argument("--label", default="baseline")
    parser.add_argument("--corpora", type=Path, default=DEFAULT_CORPORA)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD_PATH)
    parser.add_argument("--datasets", type=Path, default=DATASETS_ROOT)
    parser.add_argument("--out", type=Path, default=Path("runs/eval"))
    sys.exit(asyncio.run(run(parser.parse_args())))


if __name__ == "__main__":
    main()
