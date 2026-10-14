#!/usr/bin/env python3
"""Run UniAgent retrieval on the three spot-check datasets and compare it.

The comparison follows the evaluation described in ``slide/main.tex`` in the
parent PP04 workspace:

* graded nDCG@10 with the original 0--3 qrel labels and linear gain;
* Recall@30 with relevance thresholds 1 and 2;
* Judged@10 and Judged@30 to expose incomplete-pool bias;
* paired bootstrap confidence intervals and a paired two-sided randomization
  test over per-query nDCG@10 differences.

The old UniAgent run and the two pipeline runs that formed the slide's final
pool are read from disk.  This script only executes the new Task 2 retrieval:
BM25 candidates, GTE reranking of the top 20 chunks, and weighted RRF 0.3/0.7.
Passage results are collapsed to documents using the best fused passage score.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import gzip
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


SCRIPT_PATH = Path(__file__).resolve()
UNIAGENT_ROOT = SCRIPT_PATH.parent
CLONE_ROOT = UNIAGENT_ROOT.parent
DEFAULT_WORKSPACE_ROOT = CLONE_ROOT.parent

# Make ``src`` importable when the script is launched from any directory.
sys.path.insert(0, str(UNIAGENT_ROOT))

from src import config  # noqa: E402


DATASETS = (
    "retrieval-de-spot-check",
    "retrieval-en-spot-check",
    "retrieval-hessian-law-de-spot-check",
)
DATASET_LANGUAGES = {
    "retrieval-de-spot-check": "de",
    "retrieval-en-spot-check": "en",
    "retrieval-hessian-law-de-spot-check": "de",
}
CORPUS_PREPARATION_ALIASES = {
    "retrieval-hessian-law-de-spot-check": "retrieval-hessian-law-de-spot-check-de",
}
OLD_RUN_NAME = "uniagent-hybrid"
NEW_RUN_NAME = "uniagent-bm25-gte"
BASELINE_RUN_NAME = "weighted-rrf-mq10"
ANCHOR_RUN_NAME = "weighted-rrf-no-mq"
DEFAULT_BASELINE_ARTIFACT = (
    "recursive800-weighted-rrf-mq10-comparison-3d6715f8-3dff3c2d"
)
DEFAULT_CANONICAL_QRELS = "repaired-evaluation-v2/canonical-qrels"

METRIC_COLUMNS = (
    "ndcg@10",
    "recall@30_rel>=1",
    "recall@30_rel>=2",
    "judged@10",
    "judged@30",
)


@dataclass(frozen=True)
class DatasetPaths:
    name: str
    dataset: Path
    seed_qrels: Path
    baseline_source: Path
    anchor_source: Path
    old_source: Path
    baseline_run: Path
    anchor_run: Path
    old_run: Path
    new_run: Path
    judgments: Path
    pooled_qrels: Path
    comparison: Path


@dataclass(frozen=True)
class Evaluator:
    EvaluationSettings: type
    evaluate_query: Any
    load_qrels: Any
    load_run: Any
    pairwise_comparisons: Any
    get_pool: Any
    prepare_requests: Any
    judge_with_umbrela: Any
    write_qrels: Any
    parser_version: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help=(
            "Original PP04 workspace containing data/, outputs/, tools/, and slide/ "
            f"(default: {DEFAULT_WORKSPACE_ROOT})"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=CLONE_ROOT / "runs" / "three-dataset-retrieval-comparison",
        help="Directory for new runs and comparison reports.",
    )
    parser.add_argument(
        "--old-runs-root",
        type=Path,
        help=(
            "Existing old-pipeline output root. It must contain "
            "<dataset>/runs/uniagent-hybrid/run.txt.gz. Defaults to --output."
        ),
    )
    parser.add_argument(
        "--seed-qrels-source",
        "--qrels-source",
        dest="seed_qrels_source",
        choices=("pipeline", "canonical"),
        default="pipeline",
        help=(
            "Labels reused before UMBRELA judges newly pooled pairs: the final "
            "pipeline pool or the broader canonical qrels from slide 3."
        ),
    )
    parser.add_argument(
        "--pool-depth",
        type=int,
        default=30,
        help="Documents contributed by each run to the shared judgment pool.",
    )
    parser.add_argument(
        "--umbrela-python",
        type=Path,
        help=(
            "Python 3.12 interpreter with pooled_retrieval_eval[umbrela]. "
            "Defaults to <workspace>/.venv-umbrela."
        ),
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help=(
            "File containing OPENAI_API_KEY, OPENAI_BASE_URL, and OPENAI_MODEL. "
            "Defaults to tools/pooled_retrieval_eval/.env when present."
        ),
    )
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Build runs, the shared pool, requests, and review CSV without calling UMBRELA.",
    )
    parser.add_argument(
        "--retrieval-depth",
        type=int,
        default=config.RETRIEVAL_DEPTH,
        help="BM25 candidate chunks retained per query before GTE reranking.",
    )
    parser.add_argument(
        "--run-depth",
        type=int,
        default=config.RETRIEVAL_DEPTH,
        help="Maximum parent documents written per query.",
    )
    parser.add_argument(
        "--rrf-k",
        type=int,
        default=config.RETRIEVAL_RRF_K,
        help="RRF rank constant used to fuse BM25 and GTE passage rankings.",
    )
    parser.add_argument(
        "--bootstrap-samples",
        type=int,
        default=10_000,
        help="Samples for paired bootstrap and randomization tests.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2026,
        help="Random seed for paired significance tests.",
    )
    parser.add_argument(
        "--evaluation-only",
        action="store_true",
        help=(
            "Reuse generated UniAgent runs, resume pooled judging if needed, and "
            "rebuild reports without indexing or embedding inference."
        ),
    )
    return parser.parse_args()


def require_positive(value: int, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def configure_retrieval_java(workspace: Path) -> None:
    """Prefer the workspace's bundled JDK 21 before importing PyTerrier."""
    bundled_java = workspace / ".venv-umbrela" / "Library" / "lib" / "jvm"
    if not bundled_java.is_dir():
        return
    os.environ["JAVA_HOME"] = str(bundled_java)
    java_bin = str(bundled_java / "bin")
    path_parts = os.environ.get("PATH", "").split(os.pathsep)
    if java_bin.casefold() not in {part.casefold() for part in path_parts}:
        os.environ["PATH"] = java_bin + os.pathsep + os.environ.get("PATH", "")


def resolve_dataset_paths(
    workspace: Path,
    output: Path,
    old_runs_root: Path,
    *,
    seed_qrels_source: str,
) -> list[DatasetPaths]:
    data_root = workspace / "data"
    baseline_root = workspace / "outputs" / DEFAULT_BASELINE_ARTIFACT
    canonical_root = workspace / "outputs" / DEFAULT_CANONICAL_QRELS
    resolved: list[DatasetPaths] = []

    for name in DATASETS:
        dataset = data_root / name
        seed_qrels = (
            baseline_root / name / "pooled-judgments" / "qrels.txt"
            if seed_qrels_source == "pipeline"
            else canonical_root / name / "qrels.txt"
        )
        baseline_source = (
            baseline_root / name / "runs" / BASELINE_RUN_NAME / "run.txt.gz"
        )
        anchor_source = (
            baseline_root / name / "runs" / ANCHOR_RUN_NAME / "run.txt.gz"
        )
        old_source = old_runs_root / name / "runs" / OLD_RUN_NAME / "run.txt.gz"
        baseline_run = output / name / "runs" / BASELINE_RUN_NAME / "run.txt.gz"
        anchor_run = output / name / "runs" / ANCHOR_RUN_NAME / "run.txt.gz"
        old_run = output / name / "runs" / OLD_RUN_NAME / "run.txt.gz"
        new_run = output / name / "runs" / NEW_RUN_NAME / "run.txt.gz"
        judgments = output / name / "pooled-judgments"
        pooled_qrels = judgments / "qrels.txt"
        comparison = output / name / "comparison"

        required = {
            "queries": dataset / "queries.jsonl",
            "documents": dataset / "documents.jsonl.gz",
            f"{seed_qrels_source} seed qrels": seed_qrels,
            "existing pipeline run": baseline_source,
            "existing no-MQ anchor run": anchor_source,
            "existing old UniAgent run": old_source,
        }
        missing = [f"{label}: {path}" for label, path in required.items() if not path.is_file()]
        if missing:
            raise FileNotFoundError("Missing input(s):\n  " + "\n  ".join(missing))

        resolved.append(
            DatasetPaths(
                name,
                dataset,
                seed_qrels,
                baseline_source,
                anchor_source,
                old_source,
                baseline_run,
                anchor_run,
                old_run,
                new_run,
                judgments,
                pooled_qrels,
                comparison,
            )
        )
    return resolved


def load_queries(path: Path) -> list[dict[str, Any]]:
    queries: list[dict[str, Any]] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            try:
                item = json.loads(raw_line)
                qid = str(item["qid"])
                lexical_text = str(item["query"]).strip()
                original = item["original_query"]
                description_text = str(original["description"]).strip()
            except (json.JSONDecodeError, KeyError, TypeError) as error:
                raise ValueError(f"Invalid query row in {path}:{line_number}") from error
            if not lexical_text or not description_text:
                raise ValueError(f"Empty query/description in {path}:{line_number}")
            if qid in seen:
                raise ValueError(f"Duplicate query ID {qid!r} in {path}")
            seen.add(qid)
            queries.append(item)
    if not queries:
        raise ValueError(f"No queries in {path}")
    return sorted(queries, key=lambda item: qid_sort_key(str(item["qid"])))


def qid_sort_key(qid: str) -> tuple[int, int | str]:
    return (0, int(qid)) if qid.isdigit() else (1, qid)


def collapse_passages_to_documents(
    hits: Iterable[Any], *, depth: int
) -> list[tuple[str, float]]:
    """Use the highest-scoring fused passage as each parent document's score."""
    best: dict[str, float] = {}
    for hit in hits:
        doc_id = hit.passage.doc_id
        previous = best.get(doc_id)
        if previous is None or hit.score > previous:
            best[doc_id] = hit.score
    return sorted(best.items(), key=lambda item: (-item[1], item[0]))[:depth]


def write_trec_run(
    path: Path, rankings: dict[str, list[tuple[str, float]]], *, tag: str
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with gzip.open(temporary, "wt", encoding="utf-8", newline="\n") as handle:
        for qid in sorted(rankings, key=qid_sort_key):
            for rank, (docno, score) in enumerate(rankings[qid]):
                handle.write(f"{qid} Q0 {docno} {rank} {score:.17g} {tag}\n")
    temporary.replace(path)


def atomic_copy(source: Path, destination: Path) -> None:
    """Copy a run artifact without leaving a partial destination."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and file_sha256(destination) == file_sha256(source):
        return
    temporary = destination.with_name(destination.name + ".tmp")
    shutil.copy2(source, temporary)
    temporary.replace(destination)


def stage_existing_runs(paths: list[DatasetPaths]) -> None:
    for item in paths:
        atomic_copy(item.baseline_source, item.baseline_run)
        atomic_copy(item.anchor_source, item.anchor_run)
        atomic_copy(item.old_source, item.old_run)


async def build_new_runs(
    paths: list[DatasetPaths], *, retrieval_depth: int, run_depth: int, rrf_k: int
) -> dict[str, dict[str, Any]]:
    # Keep heavyweight Java/PyTorch imports out of --help and --evaluation-only.
    from src.retrieval.corpora import PreparedCorpus, _load_or_prepare_corpus
    from src.retrieval.fusion import (
        fuse_by_reciprocal_rank,
        weighted_fuse_by_reciprocal_rank,
    )
    from src.retrieval.lexical import LexicalIndex
    from src.retrieval.rerank import GteReranker, load_gte_model

    # UniAgent infers language from an exact ``-de``/``-en`` suffix or a
    # document-level ``language`` field.  The Hessian benchmark has neither:
    # its directory ends in ``-de-spot-check`` and its documents omit the
    # field.  Give only the preparation call a language-bearing alias, then
    # restore the real corpus name on every passage.  This keeps the original
    # retrieval implementation and source datasets unchanged.
    prepared_results = await asyncio.gather(
        *(
            asyncio.to_thread(
                _load_or_prepare_corpus,
                CORPUS_PREPARATION_ALIASES.get(item.name, item.name),
                item.dataset / "documents.jsonl.gz",
            )
            for item in paths
        )
    )
    corpora: dict[str, PreparedCorpus] = {}
    for item, (_, prepared) in zip(paths, prepared_results, strict=True):
        expected_language = DATASET_LANGUAGES[item.name]
        if prepared.language != expected_language:
            raise ValueError(
                f"Expected language {expected_language!r} for {item.name!r}, "
                f"got {prepared.language!r}"
            )
        passages = {
            passage_id: replace(passage, corpus=item.name)
            for passage_id, passage in prepared.passages.items()
        }
        corpora[item.name] = PreparedCorpus(passages, prepared.language)

    print("Building shared BM25 indexes and loading GTE...", flush=True)
    lexical, gte_model = await asyncio.gather(
        LexicalIndex.build(corpora, list(DATASETS)),
        asyncio.to_thread(load_gte_model, config.GTE_MAX_LENGTH),
    )
    reranker = GteReranker(
        gte_model,
        depth=config.GTE_RERANK_DEPTH,
        batch_size=config.GTE_BATCH_SIZE,
    )

    metadata: dict[str, dict[str, Any]] = {}
    for item in paths:
        queries = load_queries(item.dataset / "queries.jsonl")
        rankings: dict[str, list[tuple[str, float]]] = {}

        print(f"Retrieving {len(queries)} queries for {item.name}...", flush=True)
        for query in queries:
            qid = str(query["qid"])
            lexical_text = str(query["query"]).strip()
            description = str(query["original_query"]["description"]).strip()
            lexical_hits = lexical.retrievers[item.name].search(
                lexical_text,
                depth=retrieval_depth,
                wmodel=config.RETRIEVAL_WMODEL,
            )
            sparse_hits = fuse_by_reciprocal_rank(
                [lexical_hits], rrf_k=rrf_k
            )
            semantic_query = f"{lexical_text} {description}"
            gte_hits = reranker.rerank(
                sparse_hits,
                {DATASET_LANGUAGES[item.name]: [semantic_query]},
                lambda _: DATASET_LANGUAGES[item.name],
            )
            fused = weighted_fuse_by_reciprocal_rank(
                (
                    (sparse_hits, config.RETRIEVAL_SPARSE_WEIGHT),
                    (gte_hits, config.RETRIEVAL_GTE_WEIGHT),
                ),
                rrf_k=rrf_k,
            )
            rankings[qid] = collapse_passages_to_documents(fused, depth=run_depth)

        write_trec_run(item.new_run, rankings, tag=NEW_RUN_NAME)
        per_query_depths = [len(values) for values in rankings.values()]
        metadata[item.name] = {
            "queries": len(rankings),
            "min_run_depth": min(per_query_depths),
            "max_run_depth": max(per_query_depths),
            "run": str(item.new_run),
            "sha256": file_sha256(item.new_run),
        }
        print(f"Wrote {item.new_run}", flush=True)
    return metadata


def load_original_evaluator(workspace: Path) -> Evaluator:
    source = workspace / "tools" / "pooled_retrieval_eval" / "src"
    if not source.is_dir():
        raise FileNotFoundError(
            "Cannot find the slide's original evaluator source: " f"{source}"
        )
    sys.path.insert(0, str(source))
    evaluation = importlib.import_module("pooled_retrieval_eval.evaluation")
    io_module = importlib.import_module("pooled_retrieval_eval.io")
    judging = importlib.import_module("pooled_retrieval_eval.judging")
    pooling = importlib.import_module("pooled_retrieval_eval.pooling")
    response_parser = importlib.import_module("pooled_retrieval_eval.response_parser")
    return Evaluator(
        EvaluationSettings=evaluation.EvaluationSettings,
        evaluate_query=evaluation.evaluate_query,
        load_qrels=evaluation.load_qrels,
        load_run=io_module.load_run,
        pairwise_comparisons=evaluation.pairwise_comparisons,
        get_pool=pooling.get_pool,
        prepare_requests=judging.prepare_requests,
        judge_with_umbrela=judging.judge_with_umbrela,
        write_qrels=judging.write_qrels,
        parser_version=response_parser.PARSER_VERSION,
    )


def read_env_file(path: Path, environment: dict[str, str]) -> None:
    """Load a small dotenv file without printing or persisting secrets."""
    with path.open(encoding="utf-8-sig") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].lstrip()
            if "=" not in line:
                raise ValueError(f"Invalid environment row in {path}:{line_number}")
            name, value = line.split("=", 1)
            name, value = name.strip(), value.strip()
            if value[:1] == value[-1:] and value[:1] in {"'", '"'}:
                value = value[1:-1]
            if name and name not in environment:
                environment[name] = value


def resolve_umbrela_python(workspace: Path, requested: Path | None) -> Path:
    candidates = (
        [requested.expanduser().resolve()]
        if requested is not None
        else [
            workspace / ".venv-umbrela" / "python.exe",
            workspace / ".venv-umbrela" / "Scripts" / "python.exe",
            workspace / ".venv-umbrela" / "bin" / "python",
        ]
    )
    interpreter = next((path for path in candidates if path.is_file()), None)
    if interpreter is None:
        raise FileNotFoundError(
            "Python 3.12 with UMBRELA was not found. Pass --umbrela-python or "
            "create <workspace>/.venv-umbrela as documented in "
            "tools/pooled_retrieval_eval/README.md."
        )
    return interpreter.resolve()


def umbrela_environment(
    workspace: Path, interpreter: Path, env_file: Path | None
) -> dict[str, str]:
    environment = dict(os.environ)
    selected_env_file = (
        env_file.expanduser().resolve()
        if env_file is not None
        else workspace / "tools" / "pooled_retrieval_eval" / ".env"
    )
    if selected_env_file.is_file():
        read_env_file(selected_env_file, environment)
    elif env_file is not None:
        raise FileNotFoundError(f"Environment file does not exist: {selected_env_file}")

    missing = [
        name
        for name in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL")
        if not environment.get(name, "").strip()
    ]
    if missing:
        raise ValueError(
            "Missing UMBRELA provider setting(s): " + ", ".join(missing)
        )

    environment_root = (
        interpreter.parent.parent
        if interpreter.parent.name.casefold() in {"scripts", "bin"}
        else interpreter.parent
    )
    bundled_java = environment_root / "Library" / "lib" / "jvm"
    if bundled_java.is_dir():
        environment["JAVA_HOME"] = str(bundled_java)
        environment["PATH"] = str(bundled_java / "bin") + os.pathsep + environment.get(
            "PATH", ""
        )

    evaluator_source = workspace / "tools" / "pooled_retrieval_eval" / "src"
    old_pythonpath = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = str(evaluator_source) + (
        os.pathsep + old_pythonpath if old_pythonpath else ""
    )
    return environment


def validate_umbrela_runtime(interpreter: Path, environment: dict[str, str]) -> None:
    command = [
        str(interpreter),
        "-c",
        (
            "import sys; "
            "assert sys.version_info[:2] == (3, 12), sys.version; "
            "import click, openai, pyserini, umbrela"
        ),
    ]
    subprocess.run(command, check=True, env=environment)


def audit_parser_versions(
    item: DatasetPaths, pool: dict[str, list[str]], *, expected: str
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for qid, expected_docnos in pool.items():
        response_path = item.judgments / "responses" / f"{qid}.json"
        if not response_path.is_file():
            raise ValueError(f"Missing UMBRELA response: {response_path}")
        response = json.loads(response_path.read_text(encoding="utf-8-sig"))
        judgments = response.get("judgments")
        if not isinstance(judgments, list):
            raise ValueError(f"Invalid UMBRELA response: {response_path}")
        actual_docnos = [str(row.get("docno")) for row in judgments]
        if actual_docnos != expected_docnos:
            raise ValueError(f"Response does not match pool order: {response_path}")
        for row in judgments:
            judge = row.get("judge")
            if not isinstance(judge, dict):
                raise ValueError(f"Judgment has no provenance: {response_path}")
            version = str(judge.get("parser_version", ""))
            if version != expected:
                raise ValueError(
                    f"Expected parser version {expected}, found {version!r} in {response_path}"
                )
            source = str(judge.get("source", "umbrela-raw-response"))
            counts[source] = counts.get(source, 0) + 1
    return counts


def prepare_and_judge(
    paths: list[DatasetPaths],
    evaluator: Evaluator,
    workspace: Path,
    *,
    pool_depth: int,
    prepare_only: bool,
    requested_python: Path | None,
    env_file: Path | None,
) -> dict[str, dict[str, Any]]:
    states: list[tuple[DatasetPaths, dict[str, list[str]], dict[str, dict[str, int]]]] = []
    metadata: dict[str, dict[str, Any]] = {}
    total_new_pairs = 0

    for item in paths:
        runs_root = item.new_run.parents[1]
        pool = evaluator.get_pool(
            runs_root,
            pool_depth,
            item.judgments / "pools",
        )
        evaluator.prepare_requests(item.dataset, pool, item.judgments)
        seed = evaluator.load_qrels(item.seed_qrels)
        pooled_pairs = sum(len(docnos) for docnos in pool.values())
        reused_pairs = sum(
            docno in seed.get(qid, {})
            for qid, docnos in pool.items()
            for docno in docnos
        )
        new_pairs = pooled_pairs - reused_pairs
        total_new_pairs += new_pairs
        metadata[item.name] = {
            "pool_depth": pool_depth,
            "pool_pairs": pooled_pairs,
            "seed_pairs_reused": reused_pairs,
            "new_pairs_for_umbrela": new_pairs,
            "seed_qrels": str(item.seed_qrels),
            "judgments": str(item.judgments),
        }
        states.append((item, pool, seed))
        print(
            f"Prepared {item.name}: {pooled_pairs} pooled pairs, "
            f"{reused_pairs} seeded, {new_pairs} for UMBRELA.",
            flush=True,
        )

    if prepare_only:
        print(
            f"Prepare-only: {total_new_pairs} new query-document pairs require UMBRELA.",
            flush=True,
        )
        return metadata

    interpreter: Path | None = None
    environment: dict[str, str] | None = None
    if total_new_pairs:
        interpreter = resolve_umbrela_python(workspace, requested_python)
        environment = umbrela_environment(workspace, interpreter, env_file)
        validate_umbrela_runtime(interpreter, environment)

    for item, pool, seed in states:
        if metadata[item.name]["new_pairs_for_umbrela"]:
            assert interpreter is not None and environment is not None
            command = [
                str(interpreter),
                "-m",
                "pooled_retrieval_eval",
                "judge",
                "--output",
                str(item.judgments),
                "--k",
                str(pool_depth),
                "--backend",
                "umbrela",
                "--seed-qrels",
                str(item.seed_qrels),
            ]
            print(f"Judging new pairs for {item.name} with UMBRELA...", flush=True)
            subprocess.run(command, check=True, env=environment)
        else:
            evaluator.judge_with_umbrela(
                pool,
                item.judgments,
                seed_qrels=seed,
            )
            evaluator.write_qrels(pool, item.judgments)

        judged = evaluator.load_qrels(item.pooled_qrels)
        judged_pairs = {(qid, docno) for qid, labels in judged.items() for docno in labels}
        pooled_pair_set = {
            (qid, docno) for qid, docnos in pool.items() for docno in docnos
        }
        if judged_pairs != pooled_pair_set:
            raise ValueError(
                f"Qrels/pool mismatch for {item.name}: "
                f"missing={len(pooled_pair_set - judged_pairs)}, "
                f"extra={len(judged_pairs - pooled_pair_set)}"
            )
        sources = audit_parser_versions(
            item, pool, expected=evaluator.parser_version
        )
        metadata[item.name].update(
            {
                "qrels": str(item.pooled_qrels),
                "qrels_sha256": file_sha256(item.pooled_qrels),
                "parser_version": evaluator.parser_version,
                "judgment_sources": sources,
            }
        )
    return metadata


def evaluate_dataset(
    item: DatasetPaths,
    evaluator: Evaluator,
    *,
    bootstrap_samples: int,
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    qrels = evaluator.load_qrels(item.pooled_qrels)
    run_paths = {
        NEW_RUN_NAME: item.new_run,
        OLD_RUN_NAME: item.old_run,
        BASELINE_RUN_NAME: item.baseline_run,
    }
    settings_rel1 = evaluator.EvaluationSettings(
        cutoff=10,
        recall_cutoff=30,
        relevance_threshold=1,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
        primary_metric="ndcg",
    )
    settings_rel2 = evaluator.EvaluationSettings(
        cutoff=10,
        recall_cutoff=30,
        relevance_threshold=2,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
        primary_metric="ndcg",
    )

    per_query: list[dict[str, Any]] = []
    diagnostics: dict[str, Any] = {}
    qrel_topics = set(qrels)
    for run_name, run_path in run_paths.items():
        if not run_path.is_file():
            raise FileNotFoundError(f"Missing run file: {run_path}")
        run = evaluator.load_run(run_path)
        run_topics = set(run)
        if run_topics != qrel_topics:
            raise ValueError(
                f"Topic mismatch for {run_name}/{item.name}: "
                f"missing={sorted(qrel_topics - run_topics)}, "
                f"extra={sorted(run_topics - qrel_topics)}"
            )
        diagnostics[run_name] = {
            "path": str(run_path),
            "sha256": file_sha256(run_path),
            "topics": len(run_topics),
        }
        for qid in sorted(qrel_topics, key=qid_sort_key):
            ranking = [entry.docno for entry in run[qid]]
            rel1 = evaluator.evaluate_query(ranking, qrels[qid], settings_rel1)
            rel2 = evaluator.evaluate_query(ranking, qrels[qid], settings_rel2)
            per_query.append(
                {
                    "dataset": item.name,
                    "run": run_name,
                    "qid": qid,
                    "ndcg@10": rel1["ndcg@10"],
                    "recall@30_rel>=1": rel1["recall@30"],
                    "recall@30_rel>=2": rel2["recall@30"],
                    "judged@10": rel1["judged@10"],
                    "judged@30": rel1["judged@30"],
                }
            )

    summary = summarize(per_query)
    statistics_rows = evaluator.pairwise_comparisons(per_query, settings_rel1)
    return summary, per_query, {
        "pairwise": statistics_rows,
        "diagnostics": diagnostics,
        "qrels": str(item.pooled_qrels),
        "qrels_sha256": file_sha256(item.pooled_qrels),
        "qrels_pairs": sum(len(labels) for labels in qrels.values()),
        "topics": len(qrels),
    }


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    run_names = sorted({str(row["run"]) for row in rows})
    summary: list[dict[str, Any]] = []
    for run_name in run_names:
        selected = [row for row in rows if row["run"] == run_name]
        summary.append(
            {
                "run": run_name,
                **{
                    metric: mean(float(row[metric]) for row in selected)
                    for metric in METRIC_COLUMNS
                },
                "queries": len(selected),
            }
        )
    return sorted(summary, key=lambda row: row["ndcg@10"], reverse=True)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def report_markdown(
    title: str,
    summary: list[dict[str, Any]],
    pairwise: list[dict[str, Any]],
    *,
    qrels_description: str,
    bootstrap_samples: int,
) -> str:
    lines = [
        f"# {title}\n\n",
        f"Qrels: {qrels_description}\n\n",
        (
            "Metrics follow `slide/main.tex`: graded nDCG@10 keeps labels 0--3 "
            "with linear gain; Recall@30 is reported at relevance thresholds 1 and 2.\n\n"
        ),
        "| Run | R@30 rel>=1 | R@30 rel>=2 | nDCG@10 | judged@10 | judged@30 |\n",
        "|---|---:|---:|---:|---:|---:|\n",
    ]
    for row in summary:
        lines.append(
            f"| {row['run']} | {row['recall@30_rel>=1']:.6f} | "
            f"{row['recall@30_rel>=2']:.6f} | {row['ndcg@10']:.6f} | "
            f"{row['judged@10']:.6f} | {row['judged@30']:.6f} |\n"
        )

    lines.extend(
        [
            "\n## Paired nDCG@10 comparison\n\n",
            (
                f"The interval uses {bootstrap_samples:,} paired bootstrap samples. "
                "The p-value uses the paired two-sided randomization test from the "
                "original PP04 evaluator.\n\n"
            ),
            "| A | B | delta A-B | 95% CI | p | W/T/L |\n",
            "|---|---|---:|---:|---:|---:|\n",
        ]
    )
    for row in pairwise:
        lines.append(
            f"| {row['run_a']} | {row['run_b']} | "
            f"{row['mean_delta_a_minus_b']:+.6f} | "
            f"[{row['ci95_low']:+.6f}, {row['ci95_high']:+.6f}] | "
            f"{row['randomization_p']:.4f} | "
            f"{row['a_wins']}/{row['ties']}/{row['a_losses']} |\n"
        )

    if any(float(row["judged@30"]) < 1.0 for row in summary):
        lines.extend(
            [
                "\n## Pool coverage warning\n\n",
                (
                    "Judged@30 below 1 means the run retrieved documents outside the "
                    "shared pool. They are treated as non-relevant by this comparison, "
                    "so effectiveness is a lower bound until the shared pool is judged again.\n"
                ),
            ]
        )
    return "".join(lines)


def write_evaluation_report(
    output: Path,
    title: str,
    summary: list[dict[str, Any]],
    per_query: list[dict[str, Any]],
    details: dict[str, Any],
    *,
    qrels_description: str,
    bootstrap_samples: int,
) -> None:
    pairwise = details["pairwise"]
    write_csv(output / "summary.csv", summary)
    write_csv(output / "per-query.csv", per_query)
    write_csv(output / "pairwise.csv", pairwise)
    payload = {
        "metrics": {
            "ndcg@10": "graded labels 0-3, linear gain",
            "recall@30_rel>=1": "binary recall with qrel >= 1",
            "recall@30_rel>=2": "binary recall with qrel >= 2",
            "judged@10": "fraction of top 10 present in qrels",
            "judged@30": "fraction of top 30 present in qrels",
        },
        "summary": summary,
        **details,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "report.md").write_text(
        report_markdown(
            title,
            summary,
            pairwise,
            qrels_description=qrels_description,
            bootstrap_samples=bootstrap_samples,
        ),
        encoding="utf-8",
    )


def evaluate_all(
    paths: list[DatasetPaths],
    workspace: Path,
    output: Path,
    *,
    bootstrap_samples: int,
    seed: int,
) -> dict[str, Any]:
    evaluator = load_original_evaluator(workspace)
    combined_rows: list[dict[str, Any]] = []
    dataset_results: dict[str, Any] = {}

    for item in paths:
        summary, per_query, details = evaluate_dataset(
            item,
            evaluator,
            bootstrap_samples=bootstrap_samples,
            seed=seed,
        )
        write_evaluation_report(
            item.comparison,
            f"UniAgent retrieval versus slide pipeline: {item.name}",
            summary,
            per_query,
            details,
            qrels_description=f"UMBRELA/parser-v2 shared pool: `{item.pooled_qrels}`",
            bootstrap_samples=bootstrap_samples,
        )
        combined_rows.extend(
            {**row, "qid": f"{item.name}/{row['qid']}"} for row in per_query
        )
        dataset_results[item.name] = {
            "summary": summary,
            **details,
            "report": str(item.comparison / "report.md"),
        }
        print_summary(item.name, summary)

    overall_summary = summarize(combined_rows)
    settings = evaluator.EvaluationSettings(
        cutoff=10,
        recall_cutoff=30,
        relevance_threshold=1,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
        primary_metric="ndcg",
    )
    overall_pairwise = evaluator.pairwise_comparisons(combined_rows, settings)
    overall_output = output / "reports" / "cross-dataset"
    overall_details = {
        "pairwise": overall_pairwise,
        "topics": len({str(row["qid"]) for row in combined_rows}),
        "datasets": list(DATASETS),
        "qrels_pairs": sum(result["qrels_pairs"] for result in dataset_results.values()),
    }
    write_evaluation_report(
        overall_output,
        "UniAgent retrieval versus slide pipeline: all three datasets",
        overall_summary,
        combined_rows,
        overall_details,
        qrels_description=(
            "UMBRELA/parser-v2 shared top-30 qrels for all three datasets "
            "(macro-average over 65 queries)"
        ),
        bootstrap_samples=bootstrap_samples,
    )
    print_summary("all three datasets", overall_summary)
    return {
        "datasets": dataset_results,
        "cross_dataset": {
            "summary": overall_summary,
            **overall_details,
            "report": str(overall_output / "report.md"),
        },
    }


def print_summary(label: str, rows: list[dict[str, Any]]) -> None:
    print(f"\n{label}")
    print(
        f"{'run':<24} {'R@30 >=1':>11} {'R@30 >=2':>11} "
        f"{'nDCG@10':>11} {'judged@30':>11}"
    )
    for row in rows:
        print(
            f"{row['run']:<24} "
            f"{row['recall@30_rel>=1']:>11.6f} "
            f"{row['recall@30_rel>=2']:>11.6f} "
            f"{row['ndcg@10']:>11.6f} "
            f"{row['judged@30']:>11.6f}"
        )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


async def async_main() -> int:
    args = parse_args()
    require_positive(args.retrieval_depth, "--retrieval-depth")
    require_positive(args.run_depth, "--run-depth")
    require_positive(args.rrf_k, "--rrf-k")
    require_positive(args.pool_depth, "--pool-depth")
    require_positive(args.bootstrap_samples, "--bootstrap-samples")
    if args.run_depth < args.pool_depth:
        raise ValueError(
            f"--run-depth ({args.run_depth}) must be at least --pool-depth "
            f"({args.pool_depth})"
        )

    workspace = args.workspace_root.expanduser().resolve()
    output = args.output.expanduser().resolve()
    old_runs_root = (
        args.old_runs_root.expanduser().resolve()
        if args.old_runs_root is not None
        else output
    )
    configure_retrieval_java(workspace)
    paths = resolve_dataset_paths(
        workspace,
        output,
        old_runs_root,
        seed_qrels_source=args.seed_qrels_source,
    )

    retrieval_metadata: dict[str, dict[str, Any]] = {}
    if args.evaluation_only:
        missing = [str(item.new_run) for item in paths if not item.new_run.is_file()]
        if missing:
            raise FileNotFoundError(
                "--evaluation-only requires existing UniAgent runs:\n  "
                + "\n  ".join(missing)
            )
        retrieval_metadata = {
            item.name: {
                "run": str(item.new_run),
                "sha256": file_sha256(item.new_run),
            }
            for item in paths
        }
    else:
        retrieval_metadata = await build_new_runs(
            paths,
            retrieval_depth=args.retrieval_depth,
            run_depth=args.run_depth,
            rrf_k=args.rrf_k,
        )

    stage_existing_runs(paths)
    evaluator = load_original_evaluator(workspace)
    judging = prepare_and_judge(
        paths,
        evaluator,
        workspace,
        pool_depth=args.pool_depth,
        prepare_only=args.prepare_only,
        requested_python=args.umbrela_python,
        env_file=args.env_file,
    )

    if args.prepare_only:
        output.mkdir(parents=True, exist_ok=True)
        preparation = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "workspace_root": str(workspace),
            "seed_qrels_source": args.seed_qrels_source,
            "parser_version": evaluator.parser_version,
            "retrieval": retrieval_metadata,
            "judging": judging,
        }
        (output / "preparation.json").write_text(
            json.dumps(preparation, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\nPrepared pools and requests under: {output}")
        return 0

    evaluation = evaluate_all(
        paths,
        workspace,
        output,
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
    )
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(workspace),
        "output": str(output),
        "retrieval": {
            "lexical": {
                "model": config.RETRIEVAL_WMODEL,
                "input": "query",
                "depth": args.retrieval_depth,
            },
            "reranker": {
                "model": config.GTE_MODEL,
                "model_revision": config.GTE_MODEL_REVISION,
                "input": "query + original_query.description",
                "depth": config.GTE_RERANK_DEPTH,
            },
            "fusion": {
                "method": "weighted-reciprocal-rank-fusion",
                "rrf_k": args.rrf_k,
                "weights": {
                    "sparse": config.RETRIEVAL_SPARSE_WEIGHT,
                    "gte": config.RETRIEVAL_GTE_WEIGHT,
                },
                "unit": "passage",
            },
            "reused_old_runs_root": str(old_runs_root),
            "parent_aggregation": "maximum fused passage score",
            "run_depth": args.run_depth,
            "generated_runs": retrieval_metadata,
        },
        "judging": {
            "backend": "umbrela",
            "parser_version": evaluator.parser_version,
            "pool_depth": args.pool_depth,
            "seed_qrels_source": args.seed_qrels_source,
            "datasets": judging,
        },
        "evaluation": {
            "source": str(
                workspace
                / "tools"
                / "pooled_retrieval_eval"
                / "src"
                / "pooled_retrieval_eval"
                / "evaluation.py"
            ),
            "bootstrap_samples": args.bootstrap_samples,
            "seed": args.seed,
            **evaluation,
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nCross-dataset report: {output / 'reports' / 'cross-dataset' / 'report.md'}")
    return 0


def main() -> int:
    try:
        return asyncio.run(async_main())
    except ModuleNotFoundError as error:
        print(
            f"error: missing Python dependency {error.name!r}. "
            "Run `uv sync`, then launch with "
            "`uv run python .\\uniagent\\benchmark_retrieval.py`.",
            file=sys.stderr,
        )
        return 2
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
