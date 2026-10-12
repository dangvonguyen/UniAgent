import asyncio
import re
import time
from typing import TypeVar

import json_repair
from openai import AsyncOpenAI
from openai.types.responses import Response, ResponseInputParam
from pydantic import BaseModel, ValidationError

from .config import (
    LLM_COMPLETION_ATTEMPTS,
    LLM_MAX_CONCURRENCY,
    LLM_REASONING_EFFORT,
    LLM_TEMPERATURE,
    LLM_TIMEOUT_SECONDS,
    LLM_TOP_P,
)
from .tracelog import Trace

M = TypeVar("M", bound=BaseModel)


def _answer_text(response: Response) -> str:
    """The model's answer text.

    gpt-oss emits its final JSON on a `<|constrain|>Schema` channel, which vLLM
    surfaces as an `mcp_call` item instead of a message, leaving `output_text` empty.
    """
    if response.output_text:
        return response.output_text
    for item in response.output:
        if item.type in ("mcp_call", "function_call") and item.arguments:
            return item.arguments
    return ""


def _log(context: str, attempt: int, message: str) -> None:
    label = f"{context} " if context else ""
    print(
        f"  [llm] {label}attempt {attempt + 1}/{LLM_COMPLETION_ATTEMPTS}: {message}",
        flush=True,
    )


class LLM:
    def __init__(
        self, api_base: str, api_key: str, model: str, max_tokens: int, trace: Trace
    ) -> None:
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_base,
            timeout=LLM_TIMEOUT_SECONDS,
        )
        self._model = model
        self._max_tokens = max_tokens
        self._trace = trace
        self._semaphore = asyncio.Semaphore(LLM_MAX_CONCURRENCY)

    async def complete_json(
        self, system: str, user: str, schema: type[M], *, context: str = ""
    ) -> M:
        async with self._semaphore:
            return await self._complete_json(system, user, schema, context=context)

    async def _complete_json(
        self, system: str, user: str, schema: type[M], *, context: str = ""
    ) -> M:
        messages: ResponseInputParam = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        last_error: str | None = None

        for attempt in range(LLM_COMPLETION_ATTEMPTS):
            log_input = {"context": context, "attempt": attempt, "messages": messages}
            start = time.perf_counter()

            try:
                response = await self._client.responses.create(
                    model=self._model,
                    input=messages,
                    temperature=LLM_TEMPERATURE,
                    top_p=LLM_TOP_P,
                    reasoning={"effort": LLM_REASONING_EFFORT},
                    max_output_tokens=self._max_tokens,
                )
            except Exception as err:  # noqa: BLE001
                last_error = str(err)
                _log(
                    context,
                    attempt,
                    f"request failed after {time.perf_counter() - start:.2f}s: {last_error}",
                )
                self._trace.log(
                    "error",
                    input=log_input,
                    status="error",
                    error=last_error,
                )
                continue

            content = _answer_text(response)
            reasoning = (
                "\n\n".join(
                    part.text
                    for item in response.output
                    if item.type == "reasoning"
                    for part in (item.content or item.summary)
                )
                or None
            )
            usage = response.usage.model_dump() if response.usage else None
            try:
                cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())
                payload = json_repair.loads(cleaned)
                if not isinstance(payload, dict) or not payload:
                    raise ValueError(f"no JSON object in model output: {cleaned!r}")
                answer = schema.model_validate(payload)
            except (ValidationError, ValueError) as err:
                last_error = str(err)
                _log(
                    context,
                    attempt,
                    f"invalid answer after {time.perf_counter() - start:.2f}s "
                    f"({last_error[:120]!r}), retrying",
                )
                self._trace.log(
                    "model_call",
                    input=log_input,
                    output={
                        "content": content,
                        "reasoning": reasoning,
                        "usage": usage,
                    },
                    status="error",
                    error=last_error,
                )
                answer = None

            if answer is not None:
                tokens = usage.get("total_tokens") if usage else None
                _log(
                    context,
                    attempt,
                    f"ok in {time.perf_counter() - start:.2f}s, tokens={tokens}",
                )
                self._trace.log(
                    "model_call",
                    input=log_input,
                    output={
                        "content": answer.model_dump(),
                        "reasoning": reasoning,
                        "usage": usage,
                    },
                )
                return answer

        print(
            f"  [llm] {context + ' ' if context else ''}giving up after "
            f"{LLM_COMPLETION_ATTEMPTS} attempt(s): {last_error}; raising error",
            flush=True,
        )
        self._trace.log(
            "error",
            input=log_input,
            status="error",
            error=last_error or "LLM call failed after retries.",
        )
        raise RuntimeError(last_error or "LLM call failed after retries")
