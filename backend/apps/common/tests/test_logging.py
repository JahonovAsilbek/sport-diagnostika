import json
import logging
import logging.config
import uuid

import pytest
from django.conf import settings

from apps.common.logging import (
    JsonFormatter,
    RequestIDFilter,
    reset_request_id,
    set_request_id,
)


def _record(msg="m", args=None):
    return logging.LogRecord("apps.x", logging.INFO, "f", 1, msg, args, None)


def test_logging_dictconfig_is_valid():
    logging.config.dictConfig(settings.LOGGING)  # must not raise


def test_request_id_filter_defaults_to_dash():
    record = _record()
    assert RequestIDFilter().filter(record) is True
    assert record.request_id == "-"


def test_request_id_filter_reads_contextvar():
    token = set_request_id("abc123")
    try:
        record = _record()
        RequestIDFilter().filter(record)
        assert record.request_id == "abc123"
    finally:
        reset_request_id(token)


def test_json_formatter_emits_valid_json():
    record = _record("hi %s", ("u",))
    record.request_id = "rid1"
    doc = json.loads(JsonFormatter().format(record))
    assert doc["message"] == "hi u"
    assert doc["request_id"] == "rid1"
    assert doc["level"] == "INFO"
    assert doc["logger"] == "apps.x"


@pytest.mark.django_db
def test_request_id_generated_when_absent(client):
    resp = client.get("/api/v1/health/")
    uuid.UUID(resp["X-Request-ID"])  # a bare uuid4 hex — raises if malformed


@pytest.mark.django_db
def test_inbound_request_id_is_sanitized_and_echoed(client):
    resp = client.get("/api/v1/health/", HTTP_X_REQUEST_ID="trace-42\r\nInjected: x")
    rid = resp["X-Request-ID"]
    assert rid == "trace-42Injectedx"  # CR/LF, colon, space stripped
    assert "\n" not in rid and "\r" not in rid


@pytest.mark.django_db
def test_request_id_over_cap_is_truncated(client):
    resp = client.get("/api/v1/health/", HTTP_X_REQUEST_ID="a" * 200)
    assert len(resp["X-Request-ID"]) == 64
