# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from django.views.decorators.csrf import csrf_exempt
# from rest_framework import status
# import os

# @csrf_exempt
# @api_view(["POST"])
# def admin_login(request):
#     """Verify admin password. Frontend sends JSON body { password }."""
#     submitted_password = request.data.get("password")
#     expected_password = os.environ.get("ADMIN_PASSWORD")

#     print("Submitted password:", submitted_password)
#     print("Expected ADMIN_PASSWORD:", expected_password)

#     if not expected_password:
#         return Response({"detail": "ADMIN_PASSWORD not set in environment."},
#                         status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     if submitted_password != expected_password:
#         return Response({"detail": "Invalid password."},
#                         status=status.HTTP_401_UNAUTHORIZED)

#     return Response({"success": True})


from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

@csrf_exempt
@api_view(["POST"])
def admin_login(request):
    """
    Verify username and password.
    Frontend sends JSON body { "username": "...", "password": "..." }.
    If valid, return access and refresh tokens.
    """
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"detail": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, username=username, password=password)

    if user is None:
        return Response(
            {"detail": "Invalid credentials."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Issue JWT tokens
    refresh = RefreshToken.for_user(user)
    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "username": user.username,
        },
        status=status.HTTP_200_OK,
    )
