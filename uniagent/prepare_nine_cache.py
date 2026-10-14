#!/usr/bin/env python3
"""Prepare persistent retrieval and digest caches without deciding cases."""
import argparse
import asyncio
from pathlib import Path

from src.config import DEFAULT_MAX_TOKENS, RETRIEVAL_CORPORA_DIR, Settings
from src.digest import build_digest
from src.llm import LLM
from src.policy_digest_cache import corpus_signature
from src.retrieval import build_index
from src.rules import PROCUREMENT_RULES, TOPICS
from src.tracelog import Trace


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    a = parser.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    settings = Settings.from_env()
    root = a.input / RETRIEVAL_CORPORA_DIR
    signature = await asyncio.to_thread(corpus_signature, root)
    index = await build_index(root)
    with Trace(a.output / "warm-trace.jsonl.log.gz", settings.openai_model) as trace:
        llm = LLM(settings.openai_base_url, settings.openai_api_key,
                  settings.openai_model, a.max_tokens, trace)
        rules = await build_digest(PROCUREMENT_RULES, TOPICS["procurement"],
                                   index, llm, trace, cache_signature=signature,
                                   model_name=settings.openai_model)
    errors = [r.rule.id + ": " + r.error for r in rules if r.error]
    for r in rules:
        print(f"{r.rule.id}: {len(r.quotes)} quotes, " + (r.error or "cached"))
    if errors:
        raise SystemExit("Cache incomplete: " + "; ".join(errors))
    print("Nine policy packets ready; zero case decisions performed")


if __name__ == "__main__":
    asyncio.run(main())
