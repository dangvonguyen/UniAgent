import argparse
import json
from pathlib import Path
from typing import Any

from dedup import deduplicate_exact, normalize_text
from hybrid_retrieval import HybridReranker
from retrieval_tools import build_retrieval_tools


RRF_K = 60


def load_checks(path: Path) -> list[dict[str, Any]]:
    """Load and validate administrative check definitions."""

    with path.open("r", encoding="utf-8") as file:
        checks = json.load(file)

    if not isinstance(checks, list):
        raise ValueError(
            "administrative_checks.json must contain a JSON list."
        )

    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("Each administrative check must be an object.")

        for field in (
            "check_id",
            "description_vi",
            "queries",
            "keywords",
        ):
            if field not in check:
                raise ValueError(
                    f"Check is missing required field: {field}"
                )

        if not check["queries"]:
            raise ValueError(
                f"{check['check_id']} must contain at least one query."
            )

        if not check["keywords"]:
            raise ValueError(
                f"{check['check_id']} must contain at least one keyword."
            )

    return checks


def matched_keywords(
    text: str,
    keywords: list[str],
) -> list[str]:

    normalized_text = normalize_text(text)

    matches: list[str] = []

    for keyword in keywords:
        normalized_keyword = normalize_text(keyword)

        if (
            normalized_keyword
            and normalized_keyword in normalized_text
        ):
            matches.append(keyword)

    return matches


def matched_required_groups(
    text: str,
    required_groups: list[list[str]],
) -> list[list[str]]:

    normalized_text = normalize_text(text)

    all_group_matches: list[list[str]] = []

    for group in required_groups:
        group_matches: list[str] = []

        for keyword in group:
            normalized_keyword = normalize_text(keyword)

            if (
                normalized_keyword
                and normalized_keyword in normalized_text
            ):
                group_matches.append(keyword)

        all_group_matches.append(group_matches)

    return all_group_matches


def passes_keyword_filter(
    text: str,
    check: dict[str, Any],
) -> tuple[bool, list[str], list[list[str]]]:

    matches = matched_keywords(
        text,
        check["keywords"],
    )

    required_groups = check.get(
        "required_keyword_groups",
        [],
    )

    if not required_groups:
        return (
            bool(matches),
            matches,
            [],
        )

    group_matches = matched_required_groups(
        text,
        required_groups,
    )

    passes = all(
        bool(group)
        for group in group_matches
    )

    return (
        passes,
        matches,
        group_matches,
    )


def retrieve_check_candidates(
    check: dict[str, Any],
    retrieval_tools,
    top_n_per_query: int = 20,
) -> list[dict[str, Any]]:

    if top_n_per_query < 1 or top_n_per_query > 20:
        raise ValueError(
            "top_n_per_query must be between 1 and 20."
        )

    merged: dict[
        tuple[str, str],
        dict[str, Any],
    ] = {}

    for query in check["queries"]:
        for tool in retrieval_tools:
            raw_results = tool(
                query=query,
                max_results=top_n_per_query,
            )

            hits = json.loads(raw_results)

            for rank, hit in enumerate(
                hits,
                start=1,
            ):
                text = hit.get("text", "")

                if (
                    not isinstance(text, str)
                    or not text.strip()
                ):
                    continue

                (
                    passes,
                    keyword_matches,
                    group_matches,
                ) = passes_keyword_filter(
                    text,
                    check,
                )

                if not passes:
                    continue

                key = (
                    hit["corpus"],
                    hit["chunk_id"],
                )

                if key not in merged:
                    candidate = dict(hit)

                    candidate["check_id"] = check["check_id"]

                    candidate["bm25_rrf_score"] = 0.0

                    candidate["matched_keywords"] = []

                    candidate["matched_queries"] = []

                    candidate["matched_required_groups"] = []

                    candidate["retrieval_sources"] = []

                    merged[key] = candidate

                candidate = merged[key]

                # We deliberately fuse ranks instead of comparing
                # raw BM25 scores from separate corpus indices.
                candidate["bm25_rrf_score"] += (
                    1.0 / (RRF_K + rank)
                )

                candidate["matched_keywords"] = sorted(
                    set(
                        candidate["matched_keywords"]
                        + keyword_matches
                    )
                )

                flattened_group_matches = [
                    keyword
                    for group in group_matches
                    for keyword in group
                ]

                candidate["matched_required_groups"] = sorted(
                    set(
                        candidate["matched_required_groups"]
                        + flattened_group_matches
                    )
                )

                if query not in candidate["matched_queries"]:
                    candidate["matched_queries"].append(
                        query
                    )

                candidate["retrieval_sources"].append(
                    {
                        "tool": tool.name,
                        "query": query,
                        "rank": rank,
                        "bm25_score": hit["score"],
                    }
                )

    candidates = list(
        merged.values()
    )

    # First use fused lexical rank.
    # Number of matched keywords is a secondary tie-breaker.
    candidates.sort(
        key=lambda item: (
            item["bm25_rrf_score"],
            len(item["matched_keywords"]),
        ),
        reverse=True,
    )

    return candidates


def limit_chunks_per_document(
    candidates: list[dict[str, Any]],
    max_chunks_per_document: int = 2,
) -> list[dict[str, Any]]:

    if max_chunks_per_document <= 0:
        raise ValueError(
        )

    counts: dict[
        tuple[str, str],
        int,
    ] = {}

    kept: list[dict[str, Any]] = []

    for candidate in candidates:
        key = (
            candidate.get("corpus", ""),
            candidate.get("doc_id", ""),
        )

        current_count = counts.get(
            key,
            0,
        )

        if (
            current_count
            >= max_chunks_per_document
        ):
            continue

        counts[key] = current_count + 1

        kept.append(
            candidate
        )

    return kept


def semantic_query_for_check(
    check: dict[str, Any],
) -> str:

    semantic_query = check.get(
        "semantic_query",
        "",
    )

    if (
        isinstance(semantic_query, str)
        and semantic_query.strip()
    ):
        return semantic_query.strip()

    return " ".join(
        check["keywords"]
    )


def save_results(
    output_dir: Path,
    check: dict[str, Any],
    results: list[dict[str, Any]],
) -> Path:

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        output_dir
        / f"{check['check_id']}.jsonl"
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        for rank, result in enumerate(
            results,
            start=1,
        ):
            row = dict(result)

            row["final_rank"] = rank

            row["description_vi"] = (
                check["description_vi"]
            )

            file.write(
                json.dumps(
                    row,
                    ensure_ascii=False,
                )
                + "\n"
            )

    return path


def save_summary(
    output_dir: Path,
    summaries: list[dict[str, Any]],
) -> None:
    """Save an easy-to-read overview of the retrieval run."""

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary_path = (
        output_dir
        / "summary.json"
    )

    with summary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summaries,
            file,
            ensure_ascii=False,
            indent=2,
        )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input-root",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--checks",
        type=Path,
        default=Path(
            "administrative_checks.json"
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "artifacts/offline_retrieval"
        ),
    )

    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--final-top-k",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--max-chunks-per-document",
        type=int,
        default=2,
    )

    args = parser.parse_args()

    checks = load_checks(
        args.checks
    )

    print(
        f"Loaded {len(checks)} "
        "administrative check(s)."
    )

    print(
        "\nBuilding retrieval indexes..."
    )

    retrieval_tools = build_retrieval_tools(
        args.input_root
    )

    print(
        "\nLoading dense reranker..."
    )

    reranker = HybridReranker()

    summaries: list[
        dict[str, Any]
    ] = []

    for check in checks:
        print(
            "\n"
            + "=" * 80
        )

        print(
            f"CHECK: {check['check_id']}"
        )

        print(
            f"Meaning: "
            f"{check['description_vi']}"
        )

        candidates = retrieve_check_candidates(
            check,
            retrieval_tools,
            top_n_per_query=args.top_n,
        )

        count_after_keyword_filter = len(
            candidates
        )

        print(
            "After required keyword filter: "
            f"{count_after_keyword_filter}"
        )

        candidates = deduplicate_exact(
            candidates
        )

        count_after_dedup = len(
            candidates
        )

        print(
            "After exact dedup: "
            f"{count_after_dedup}"
        )

        candidates = limit_chunks_per_document(
            candidates,
            max_chunks_per_document=(
                args.max_chunks_per_document
            ),
        )

        count_after_document_limit = len(
            candidates
        )

        print(
            "After per-document limit: "
            f"{count_after_document_limit}"
        )

        if not candidates:
            print(
                "No passages satisfy all "
                "required keyword groups."
            )

            output_path = save_results(
                args.output_dir,
                check,
                [],
            )

            summaries.append(
                {
                    "check_id": check["check_id"],
                    "description_vi": check[
                        "description_vi"
                    ],
                    "keyword_candidates": (
                        count_after_keyword_filter
                    ),
                    "after_dedup": (
                        count_after_dedup
                    ),
                    "after_document_limit": (
                        count_after_document_limit
                    ),
                    "final_results": 0,
                    "output_file": str(
                        output_path
                    ),
                }
            )

            continue

        semantic_query = (
            semantic_query_for_check(
                check
            )
        )

        print(
            f"Semantic query: "
            f"{semantic_query}"
        )

        results = reranker.rerank(
            query=semantic_query,
            candidates=candidates,
            top_k=args.final_top_k,
        )

        print(
            "\nTOP PASSAGES:"
        )

        for rank, result in enumerate(
            results,
            start=1,
        ):
            print(
                f"\n[{rank}] "
                f"{result['corpus']} | "
                f"{result['chunk_id']}"
            )

            title = result.get(
                "title"
            )

            if title:
                print(
                    f"Title: {title}"
                )

            print(
                "Keywords: "
                + ", ".join(
                    result.get(
                        "matched_keywords",
                        [],
                    )
                )
            )

            print(
                f"Lexical rank: "
                f"{result['bm25_rank']}"
            )

            print(
                f"Dense score: "
                f"{result['dense_score']:.4f}"
            )

            print(
                f"Dense rank: "
                f"{result['dense_rank']}"
            )

            print(
                f"Hybrid score: "
                f"{result['hybrid_score']:.6f}"
            )

            preview = (
                result["text"][:500]
                .replace(
                    "\n",
                    " ",
                )
            )

            print(
                f"Text: {preview}..."
            )

        output_path = save_results(
            args.output_dir,
            check,
            results,
        )

        summaries.append(
            {
                "check_id": check["check_id"],
                "description_vi": check[
                    "description_vi"
                ],
                "keyword_candidates": (
                    count_after_keyword_filter
                ),
                "after_dedup": (
                    count_after_dedup
                ),
                "after_document_limit": (
                    count_after_document_limit
                ),
                "final_results": len(results),
                "output_file": str(
                    output_path
                ),
            }
        )

    save_summary(
        args.output_dir,
        summaries,
    )

    print(
        "\n"
        + "=" * 80
    )

    print(
        "Finished offline rule retrieval."
    )

    print(
        f"Results saved to: "
        f"{args.output_dir}"
    )

    print(
        f"Summary saved to: "
        f"{args.output_dir / 'summary.json'}"
    )


if __name__ == "__main__":
    main()