from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import os


@api_view(["POST"])
def admin_login(request):
    """Verify admin password. Frontend sends X-Admin-Password or JSON body."""
    password = (
        request.headers.get("X-Admin-Password")
        or request.data.get("password")
        or request.POST.get("password")
    )
    expected = os.environ.get("ADMIN_PASSWORD")
    if not expected or password != expected:
        return Response({"detail": "Invalid password."}, status=status.HTTP_401_UNAUTHORIZED)
    return Response({"success": True})
