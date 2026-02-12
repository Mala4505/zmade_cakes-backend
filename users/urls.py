from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("login/", admin_login, name="admin_login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
