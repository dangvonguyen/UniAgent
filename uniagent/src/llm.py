import json
import re
from typing import TypeVar

import json_repair
from openai import OpenAI
from pydantic import BaseModel, ValidationError

from .tracelog import Trace

M = TypeVar("M", bound=BaseModel)


def verified(quote: str | None, source: str) -> bool:
    """A Verified Quote is a non-empty verbatim excerpt of its source (whitespace-insensitive)."""
    normalize = lambda text: re.sub(r"\s+", " ", text or "").strip().lower()
    return bool(normalize(quote)) and normalize(quote) in normalize(source)


class LLM:
    def __init__(
        self, api_base: str, api_key: str, model: str, max_tokens: int, trace: Trace
    ) -> None:
        self._client = OpenAI(
            api_key=api_key, base_url=api_base, max_retries=2, timeout=120
        )
        self._model = model
        self._max_tokens = max_tokens
        self._trace = trace

    def complete_json(
        self, system: str, user: str, schema: type[M], *, context: str = ""
    ) -> M:
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": f"{user}\n\nJSON schema of the answer:\n{json.dumps(schema.model_json_schema(), ensure_ascii=False)}",
            },
        ]
        last_error: str | None = None

        for attempt in range(2):
            log_input = {"context": context, "attempt": attempt, "messages": messages}

            try:
                response = self._client.responses.create(
                    model=self._model,
                    input=messages,
                    temperature=0,
                    max_output_tokens=self._max_tokens,
                )
            except Exception as err:  # noqa: BLE001
                last_error = str(err)
                self._trace.log(
                    "error",
                    input=log_input,
                    status="error",
                    error=last_error,
                )
                continue

            content = response.output_text
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
                answer = schema.model_validate(json_repair.loads(content or "") or {})
            except ValidationError as err:
                last_error = str(err)
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

        self._trace.log(
            "error",
            input=log_input,
            status="error",
            error=last_error or "LLM call failed after retries; return empty answer.",
        )
        return schema()
