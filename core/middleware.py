import os
from django.http import JsonResponse


class AdminPasswordMiddleware:
    """Protect /api/admin/* routes with ADMIN_PASSWORD from request header."""

    ADMIN_PREFIX = "/api/admin/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(self.ADMIN_PREFIX):
            excluded = [
                "/api/admin/login/",
            ]
            if any(request.path == ex or request.path.rstrip("/") == ex.rstrip("/") for ex in excluded):
                return self.get_response(request)

            password = request.headers.get("X-Admin-Password") or request.POST.get("password")
            expected = os.environ.get("ADMIN_PASSWORD")
            if not expected or password != expected:
                return JsonResponse({"detail": "Invalid or missing admin password."}, status=401)

        return self.get_response(request)
