from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer


@api_view(["GET"])
def admin_notification_list(request):
    notifications = Notification.objects.filter(is_read=False).order_by("-created_at")
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def admin_notification_read(request, pk):
    notification = Notification.objects.filter(pk=pk).first()
    if notification:
        notification.is_read = True
        notification.save()
    return Response({"success": True})
