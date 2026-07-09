from apps.audit.context import bind_request, client_ip, reset


class AuditContextMiddleware:
    """Binds the request + client IP so the audit signals can attribute mutations to the acting
    user. The user itself is read lazily at signal-fire time (JWT auth resolves it in the view)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = bind_request(request, client_ip(request))
        try:
            return self.get_response(request)
        finally:
            reset(token)
