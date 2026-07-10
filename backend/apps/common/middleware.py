"""Request-id middleware (DVPS-19) — register FIRST in MIDDLEWARE so the id covers the whole
request. Mirrors the reset-in-finally shape of apps/audit/middleware.py."""

import re
import uuid

from apps.common.logging import reset_request_id, set_request_id

# Inbound X-Request-ID is client-controlled — keep only safe chars and cap the length so a
# forged value can't inject newlines into logs or the response header.
_SANITIZE = re.compile(r"[^A-Za-z0-9._-]")


class RequestIDMiddleware:
    HEADER = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = _SANITIZE.sub("", request.META.get("HTTP_X_REQUEST_ID", ""))[:64]
        rid = incoming or uuid.uuid4().hex
        token = set_request_id(rid)
        try:
            response = self.get_response(request)
            response[self.HEADER] = rid
            return response
        finally:
            reset_request_id(token)
