from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models import F
from products.models import Product
from customers.models import Customer


class BatchStock(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('closed', 'Closed'),
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        limit_choices_to={'type': 'batch'},
        related_name='batch_stocks'
    )

    start_date = models.DateField()

    total_quantity = models.PositiveIntegerField()
    booked_quantity = models.PositiveIntegerField(default=0)
    collected_quantity = models.PositiveIntegerField(default=0)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    @property
    def available_quantity(self):
        return self.total_quantity - self.booked_quantity

    def clean(self):
        if self.booked_quantity > self.total_quantity:
            raise ValidationError("Booked quantity cannot exceed total quantity.")

        if self.collected_quantity > self.booked_quantity:
            raise ValidationError("Collected quantity cannot exceed booked quantity.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.start_date} ({self.status})"


class BatchBooking(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('wamd', 'WAMD'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    )

    STATUS_CHOICES = (
        ('booked', 'Booked'),
        ('collected', 'Collected'),
        ('cancelled', 'Cancelled'),
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='batch_bookings'
    )

    batch_stock = models.ForeignKey(
        BatchStock,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    pickup_date = models.DateField()
    quantity = models.PositiveIntegerField()

    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='unpaid')

    discount = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=3, editable=False)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='booked')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")

        if self.pickup_date < self.batch_stock.start_date:
            raise ValidationError("Pickup date cannot be before batch start date.")

    def save(self, *args, **kwargs):
        with transaction.atomic():
            stock = BatchStock.objects.select_for_update().get(pk=self.batch_stock.pk)

            is_new = self.pk is None

            if not is_new:
                old_booking = BatchBooking.objects.select_for_update().get(pk=self.pk)
                old_status = old_booking.status
                old_quantity = old_booking.quantity
            else:
                old_status = None
                old_quantity = 0

            # -------------------------------------------------
            # 1️⃣ HANDLE BOOKED QUANTITY (QUANTITY NEVER EDITED)
            # -------------------------------------------------

            if is_new:
                quantity_difference = self.quantity

            elif old_status != 'cancelled' and self.status == 'cancelled':
                quantity_difference = -old_quantity

            elif old_status == 'cancelled' and self.status != 'cancelled':
                quantity_difference = self.quantity

            else:
                quantity_difference = 0  # no quantity editing allowed

            # Validate stock availability
            if quantity_difference > 0:
                if quantity_difference > stock.available_quantity:
                    raise ValidationError(
                        f"Only {stock.available_quantity} items available."
                    )

            # -------------------------------------------------
            # 2️⃣ CALCULATE TOTAL
            # -------------------------------------------------

            base_total = self.quantity * stock.product.base_price

            if self.discount < 0:
                raise ValidationError("Discount cannot be negative.")

            if self.discount > base_total:
                raise ValidationError("Discount cannot exceed total amount.")

            self.total_amount = base_total - self.discount

            super().save(*args, **kwargs)

            # Update booked_quantity
            if quantity_difference != 0:
                stock.booked_quantity = F('booked_quantity') + quantity_difference
                stock.save()
                stock.refresh_from_db()

            # -------------------------------------------------
            # 3️⃣ HANDLE COLLECTED QUANTITY (OPTION A LIVE UPDATE)
            # -------------------------------------------------

            collected_difference = 0

            if old_status != 'collected' and self.status == 'collected':
                collected_difference = self.quantity

            elif old_status == 'collected' and self.status != 'collected':
                collected_difference = -old_quantity

            if collected_difference != 0:
                stock.collected_quantity = F('collected_quantity') + collected_difference
                stock.save()
                stock.refresh_from_db()

    def __str__(self):
        return f"Booking {self.id} - {self.customer.name}"