from django.urls import path
from . import views

urlpatterns = [
    path("edit/<uuid:token>/", views.public_order_edit),
    path("view/<uuid:token>/", views.public_order_view),
]
