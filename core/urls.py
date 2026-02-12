from django.urls import path, include

urlpatterns = [
    path("api/auth/", include("users.urls")),
    path("api/admin/", include("orders.urls")),
    path("api/admin/", include("activity.urls")),
]
