from django.urls import path, include

urlpatterns = [
    path("api/admin/", include("users.urls")),
    path("api/admin/", include("orders.urls")),
    path("api/admin/", include("activity.urls")),
]
