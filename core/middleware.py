import os
from django.http import JsonResponse

class AdminPasswordMiddleware:
    """Protect /api/admin/* routes with ADMIN_PASSWORD from request header or body."""

    ADMIN_PREFIX = "/api/admin/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(self.ADMIN_PREFIX):
            # Allow login route without password check
            if request.path.rstrip("/") == "/api/admin/login":
                return self.get_response(request)

            # Check header first, then body
            password = request.headers.get("x-admin-password") or request.POST.get("password")
            if not password and hasattr(request, "data"):
                password = request.data.get("password")

            expected = os.environ.get("ADMIN_PASSWORD")

            if not expected or password != expected:
                return JsonResponse({"success": False, "detail": "Unauthorized"}, status=401)

        return self.get_response(request)
