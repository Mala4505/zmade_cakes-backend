import uuid
from decimal import Decimal
from django.db import models


ORDER_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("pending", "Pending"),
    ("customer_confirmed", "Customer Confirmed"),
    ("preparing", "Preparing"),
    ("ready", "Ready"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
]

PICKUP_OR_DELIVERY_CHOICES = [
    ("pickup", "Pickup"),
    ("delivery", "Delivery"),
]

DELIVERY_TIME_CHOICES = [
    ("morning", "Morning"),
    ("afternoon", "Afternoon"),
    ("evening", "Evening"),
]

PAYMENT_STATUS_CHOICES = [
    ("unpaid", "Unpaid"),
    ("paid", "Paid"),
]


class Order(models.Model):
    order_number = models.CharField(max_length=32, unique=True, editable=False)
    customer_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32)
    email = models.EmailField(blank=True)
    area = models.CharField(max_length=128)
    address = models.TextField(blank=True)
    pickup_or_delivery = models.CharField(max_length=16, choices=PICKUP_OR_DELIVERY_CHOICES)

    items = models.JSONField(
        default=list,
        help_text='[{"cake_type": str, "flavor": str, "size": str, "quantity": int, "price": str, "notes": str}]',
    )

    delivery_date = models.DateField()
    delivery_time = models.CharField(max_length=16, choices=DELIVERY_TIME_CHOICES)

    status = models.CharField(max_length=32, choices=ORDER_STATUS_CHOICES, default="draft")
    payment_status = models.CharField(max_length=16, choices=PAYMENT_STATUS_CHOICES, default="unpaid")
    payment_date = models.DateTimeField(null=True, blank=True)

    is_locked = models.BooleanField(default=False)
    edit_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invoice_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    admin_notes = models.TextField(blank=True)
    customer_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.order_number:
            n = Order.objects.count() + 1
            self.order_number = f"ZMC-{n:04d}"
        super().save(*args, **kwargs)

    @property
    def total(self):
        from decimal import Decimal
        t = Decimal("0")
        for item in self.items or []:
            qty = int(item.get("quantity") or 0)
            price = Decimal(str(item.get("price") or 0))
            t += price * qty
        return t

    @property
    def invoice_items(self):
        from decimal import Decimal
        result = []
        for item in self.items or []:
            qty = int(item.get("quantity") or 0)
            price = Decimal(str(item.get("price") or 0))
            result.append({
                **item,
                "line_total": price * qty,
            })
        return result

    def __str__(self):
        return self.order_number


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    old_status = models.CharField(max_length=32, blank=True)
    new_status = models.CharField(max_length=32)
    changed_by = models.CharField(max_length=16, choices=[("admin", "Admin"), ("customer", "Customer")])
    timestamp = models.DateTimeField(auto_now_add=True)


class CollateralItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="collateral_items")
    item_name = models.CharField(max_length=255)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal("0"))
    return_required = models.BooleanField(default=True)


class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="invoice")
    pdf_url = models.URLField(max_length=500, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
