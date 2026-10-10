"""Per-request context: the request id, and the patient text the request carries.

The patient-text registry backs the logging filter (PRIV-04): anything a
request or job registers here is redacted from every log record created
while it is being handled.
"""

from __future__ import annotations

import contextvars
import re
from collections.abc import Iterable, Iterator
from contextlib import contextmanager

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar("hs_request_id", default="-")
_sensitive: contextvars.ContextVar[tuple[str, ...]] = contextvars.ContextVar("hs_sensitive", default=())

# Shorter fragments would redact ordinary log words.
MIN_FRAGMENT_CHARS = 8
_CLAUSE_SPLIT = re.compile(r"[\n\r.,;:!?।|]+")


def current_request_id() -> str:
    return _request_id.get()


def set_request_id(value: str) -> contextvars.Token:
    return _request_id.set(value)


def reset_request_id(token: contextvars.Token) -> None:
    _request_id.reset(token)


def _fragments(value: str) -> Iterator[str]:
    text = " ".join(str(value).split()).lower()
    if len(text) >= MIN_FRAGMENT_CHARS:
        yield text
    for clause in _CLAUSE_SPLIT.split(text):
        clause = clause.strip()
        if len(clause) >= MIN_FRAGMENT_CHARS:
            yield clause


def mark_sensitive(*values: str | None) -> None:
    """Register patient-supplied strings for the rest of this request or job."""
    fragments = [f for value in values if value for f in _fragments(value)]
    if fragments:
        _sensitive.set(_sensitive.get() + tuple(fragments))


def begin_sensitive_scope() -> contextvars.Token:
    return _sensitive.set(())


def end_sensitive_scope(token: contextvars.Token) -> None:
    _sensitive.reset(token)


def sensitive_fragments() -> tuple[str, ...]:
    return _sensitive.get()


@contextmanager
def sensitive_scope(values: Iterable[str | None] = ()) -> Iterator[None]:
    """A fresh registry for a job running outside any request."""
    token = _sensitive.set(())
    try:
        mark_sensitive(*values)
        yield
    finally:
        _sensitive.reset(token)
