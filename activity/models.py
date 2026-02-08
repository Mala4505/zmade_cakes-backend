from django.db import models


NOTIFICATION_TYPE_CHOICES = [
    ("status", "Status"),
    ("payment", "Payment"),
    ("edit", "Edit"),
]


class Notification(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    type = models.CharField(max_length=16, choices=NOTIFICATION_TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class ActivityLog(models.Model):
    action = models.CharField(max_length=128)
    entity_type = models.CharField(max_length=64)
    entity_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
