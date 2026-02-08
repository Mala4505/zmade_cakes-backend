from django.db.models.signals import Signal
from django.dispatch import receiver

order_status_changed = Signal()
order_payment_changed = Signal()
order_edited_by_customer = Signal()


@receiver(order_status_changed)
def on_order_status_changed(sender, instance, old_status, changed_by, **kwargs):
    from .models import OrderStatusHistory
    from activity.models import Notification, ActivityLog

    OrderStatusHistory.objects.create(
        order=instance,
        old_status=old_status,
        new_status=instance.status,
        changed_by=changed_by,
    )
    Notification.objects.create(
        title=f"Order {instance.order_number} status updated",
        message=f"Status changed from {old_status} to {instance.status}",
        type="status",
    )
    ActivityLog.objects.create(
        action="status_change",
        entity_type="order",
        entity_id=str(instance.pk),
        metadata={"old_status": old_status, "new_status": instance.status, "changed_by": changed_by},
    )


@receiver(order_payment_changed)
def on_order_payment_changed(sender, instance, changed_by, **kwargs):
    from activity.models import Notification, ActivityLog

    Notification.objects.create(
        title=f"Order {instance.order_number} payment updated",
        message=f"Payment status: {instance.payment_status}",
        type="payment",
    )
    ActivityLog.objects.create(
        action="payment_change",
        entity_type="order",
        entity_id=str(instance.pk),
        metadata={"payment_status": instance.payment_status, "changed_by": changed_by},
    )


@receiver(order_edited_by_customer)
def on_order_edited_by_customer(sender, instance, **kwargs):
    from activity.models import Notification, ActivityLog

    Notification.objects.create(
        title=f"Order {instance.order_number} edited by customer",
        message="Customer made changes to the order",
        type="edit",
    )
    ActivityLog.objects.create(
        action="customer_edit",
        entity_type="order",
        entity_id=str(instance.pk),
        metadata={},
    )
