from django.urls import path
from . import views

urlpatterns = [
    path("orders/", views.admin_order_list),
    path("orders/<int:pk>/", views.admin_order_detail),
    path("orders/<int:pk>/status/", views.admin_order_status),
    path("orders/<int:pk>/payment/", views.admin_order_payment),

    path("edit/<uuid:token>/", views.public_order_edit),
    path("view/<uuid:token>/", views.public_order_view),
]
