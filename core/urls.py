from django.urls import path, include

urlpatterns = [
    path("api/admin/", include("users.urls")),
    path("api/admin/", include("orders.admin_urls")),
    path("api/admin/", include("activity.urls")),
    path("api/orders/", include("orders.public_urls")),
]
