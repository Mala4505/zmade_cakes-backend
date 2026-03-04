from django.urls import path, include

urlpatterns = [
    path("api/auth/", include("users.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/activity/", include("activity.urls")),
    path("api/products/", include("products.urls")),
    path("api/customers/", include("customers.urls")),
    path("api/batch/", include("batch.urls")),
]
