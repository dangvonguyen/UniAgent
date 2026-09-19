import contextvars
import gzip
import itertools
import json
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

_current_case: contextvars.ContextVar[str] = contextvars.ContextVar(
    "event_logging_case", default="-"
)


class Trace:
    def __init__(self, path: Path, model: str) -> None:
        self._file = gzip.open(path, "wt", encoding="utf-8")  # noqa: SIM115
        self._counter = itertools.count(1)
        self._model = model
        self._last_event: dict[str, str | None] = {}

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def log(
        self,
        event_type: str,
        *,
        tool: str | None = None,
        input: Any = None,
        output: Any = None,
        status: str = "ok",
        error: str | None = None,
    ) -> str:
        event_id = f"evt-{next(self._counter):04d}"
        case_id = _current_case.get()
        parent_event_id = self._last_event.get(case_id)
        event = {
            "case_id": case_id,
            "event_id": event_id,
            "parent_event_id": parent_event_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "model": self._model,
            "tool": tool,
            "input": input,
            "output": output,
            "status": status,
            "error": error,
        }
        self._file.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
        self._file.flush()
        self._last_event[case_id] = event_id
        return event_id

    @contextmanager
    def case(self, case_id: str) -> Generator[None]:
        case_token = _current_case.set(case_id)
        try:
            yield
        finally:
            _current_case.reset(case_token)
