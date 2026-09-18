import contextvars
import gzip
import itertools
import json
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

_AUTO = object()

_current_case: contextvars.ContextVar[str] = contextvars.ContextVar(
    "event_logging_case", default="-"
)
_current_parent: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "event_logging_parent", default=None
)


class Trace:
    def __init__(self, path: Path, model: str) -> None:
        self._file = gzip.open(path, "wt", encoding="utf-8")  # noqa: SIM115
        self._counter = itertools.count(1)
        self._model = model

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
        parent: str | None = _AUTO,  # type: ignore[assignment]
    ) -> str:
        event_id = f"evt-{next(self._counter):04d}"
        event = {
            "case_id": _current_case.get(),
            "event_id": event_id,
            "parent_event_id": _current_parent.get() if parent is _AUTO else parent,
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
        _current_parent.set(event_id)
        return event_id

    @contextmanager
    def case(self, case_id: str) -> Generator[None]:
        """Scope subsequent log() calls to case_id with a fresh (unparented) event chain."""
        case_token = _current_case.set(case_id)
        parent_token = _current_parent.set(None)
        try:
            yield
        finally:
            _current_case.reset(case_token)
            _current_parent.reset(parent_token)
