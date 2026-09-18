import json
import os
import re
from typing import TypeVar

import json_repair
from openai import OpenAI
from pydantic import BaseModel, ValidationError

M = TypeVar("M", bound=BaseModel)


def verified(quote: str | None, source: str) -> bool:
    """A Verified Quote is a non-empty verbatim excerpt of its source (whitespace-insensitive)."""
    normalize = lambda text: re.sub(r"\s+", " ", text or "").strip().lower()
    return bool(normalize(quote)) and normalize(quote) in normalize(source)


def required_environment() -> tuple[str, str, str]:
    values = []
    for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "OPENAI_MODEL"):
        value = os.environ.get(name, "").strip()
        if not value:
            raise RuntimeError(f"Required environment variable {name} is not set.")
        values.append(value)
    return values[0], values[1], values[2]


class LLM:
    def __init__(self, max_tokens: int) -> None:
        base_url, api_key, model = required_environment()

        self._client = OpenAI(
            api_key=api_key, base_url=base_url, max_retries=2, timeout=120
        )
        self._model = model
        self._max_tokens = max_tokens

    def complete_json(self, system: str, user: str, schema: type[M]) -> M:
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": f"{user}\n\nJSON schema of the answer:\n{json.dumps(schema.model_json_schema(), ensure_ascii=False)}",
            },
        ]
        for attempt in range(2):
            response = self._client.responses.create(
                model=self._model,
                input=messages,
                temperature=0,
                max_output_tokens=self._max_tokens,
            )

            content = response.output_text
            try:
                answer = schema.model_validate(json_repair.loads(content or "") or {})
            except ValidationError:
                answer = None

            if answer is not None:
                return answer

        return schema()
