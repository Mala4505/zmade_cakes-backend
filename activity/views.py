# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from .models import Notification
# from .serializers import NotificationSerializer


# @api_view(["GET"])
# def admin_notification_list(request):
#     notifications = Notification.objects.filter(is_read=False).order_by("-created_at")
#     serializer = NotificationSerializer(notifications, many=True)
#     return Response(serializer.data)


# @api_view(["POST"])
# def admin_notification_read(request, pk):
#     notification = Notification.objects.filter(pk=pk).first()
#     if notification:
#         notification.is_read = True
#         notification.save()
#     return Response({"success": True})


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Notification
from .serializers import NotificationSerializer

@api_view(["GET"])
def admin_notification_list(request):
    """Return all notifications, newest first."""
    notifications = Notification.objects.all().order_by("-created_at")
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)

@api_view(["POST"])
def admin_notification_read(request, pk):
    """Mark a single notification as read."""
    try:
        notification = Notification.objects.get(pk=pk)
        notification.is_read = True
        notification.save()
        return Response({"success": True})
    except Notification.DoesNotExist:
        return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(["POST"])
def admin_notification_mark_all_read(request):
    """Mark all notifications as read."""
    Notification.objects.filter(is_read=False).update(is_read=True)
    return Response({"success": True})
