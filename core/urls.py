from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/activity/", include("activity.urls")),
    path("api/products/", include("products.urls")),
    path("api/customers/", include("customers.urls")),
    path("api/batch/", include("batch.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)