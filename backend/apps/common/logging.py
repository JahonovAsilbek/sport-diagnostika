"""Request-id correlation for logs (DVPS-19).

A ContextVar (same pattern as apps/audit/context.py) holds a correlation id — set per web
request by RequestIDMiddleware and per Celery task by the signals below. `RequestIDFilter`
stamps it onto every log record so the formatter can print it, letting one id tie web +
worker lines together. Pure stdlib + celery, so this is safe to import while Django builds
its logging config (no models, no app registry).
"""

import json
import logging
from contextvars import ContextVar

from celery.signals import task_postrun, task_prerun

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(value):
    return _request_id.set(value)


def reset_request_id(token):
    _request_id.reset(token)


def get_request_id():
    return _request_id.get()


class RequestIDFilter(logging.Filter):
    """Stamp the current request id onto every record. Attach to the HANDLER (not loggers) so
    records propagating up from child loggers are stamped too."""

    def filter(self, record):
        record.request_id = get_request_id() or "-"
        return True


class JsonFormatter(logging.Formatter):
    """Minimal structured JSON — no third-party dependency (stdlib ships no JSON formatter)."""

    def format(self, record):
        payload = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


# Reuse the same contextvar in the worker so task logs carry the task id (with root-logger
# hijack disabled, Celery's own %(task_id)s isn't injected — this fills that gap).
@task_prerun.connect
def _bind_task_request_id(task_id=None, **_):
    set_request_id(task_id)


@task_postrun.connect
def _clear_task_request_id(**_):
    set_request_id(None)
