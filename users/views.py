# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from django.views.decorators.csrf import csrf_exempt
# from rest_framework import status
# import os

# @csrf_exempt
# # @require_POST
# @api_view(["POST"])
# def admin_login(request):
#     """Verify admin password. Frontend sends X-Admin-Password or JSON body."""
#     password = (
#         request.headers.get("X-Admin-Password")
#         or request.data.get("password")
#         or request.POST.get("password")
#     )
#     expected = os.environ.get("ADMIN_PASSWORD")
    
#     print("Submitted password:", password)
#     print("Expected ADMIN_PASSWORD:", expected)
    
#     if not expected or password != expected:
#         return Response({"detail": "Invalid password."}, status=status.HTTP_401_UNAUTHORIZED)
#     return Response({"success": True})


from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
import os

@csrf_exempt
@api_view(["POST"])
def admin_login(request):
    """Verify admin password. Frontend sends JSON body { password }."""
    submitted_password = request.data.get("password")
    expected_password = os.environ.get("ADMIN_PASSWORD")

    print("Submitted password:", submitted_password)
    print("Expected ADMIN_PASSWORD:", expected_password)

    if not expected_password:
        return Response({"detail": "ADMIN_PASSWORD not set in environment."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if submitted_password != expected_password:
        return Response({"detail": "Invalid password."},
                        status=status.HTTP_401_UNAUTHORIZED)

    return Response({"success": True})
