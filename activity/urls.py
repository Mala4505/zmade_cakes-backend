from django.urls import path
from . import views

urlpatterns = [
    path("notifications/", views.admin_notification_list),
    path("notifications/<int:pk>/read/", views.admin_notification_read),
]
