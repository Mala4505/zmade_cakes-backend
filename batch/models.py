from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
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

    # DEPRECATED — kept for data migration only. Do not update these in new code.
    total_quantity = models.PositiveIntegerField(default=0)
    booked_quantity = models.PositiveIntegerField(default=0)
    collected_quantity = models.PositiveIntegerField(default=0)

    # Piece-based fields — use these in all new code
    total_pieces = models.PositiveIntegerField(
        default=0,
        help_text="Total individual pieces baked for this batch (e.g. 240 brownies)"
    )
    booked_pieces = models.PositiveIntegerField(
        default=0,
        help_text="Pieces committed across all active bookings. Updated atomically."
    )
    collected_pieces = models.PositiveIntegerField(
        default=0,
        help_text="Pieces physically collected. Updated when booking status → collected."
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    @property
    def available_pieces(self):
        return self.total_pieces - self.booked_pieces

    # Kept for backward compatibility with any old code still referencing it
    @property
    def available_quantity(self):
        return self.total_quantity - self.booked_quantity

    def clean(self):
        # Deprecated field validation (kept while old data still exists)
        if self.booked_quantity > self.total_quantity:
            raise ValidationError("Booked quantity cannot exceed total quantity.")
        if self.collected_quantity > self.booked_quantity:
            raise ValidationError("Collected quantity cannot exceed booked quantity.")

        # Piece-based validation
        if self.booked_pieces > self.total_pieces:
            raise ValidationError("Booked pieces cannot exceed total pieces.")
        if self.collected_pieces > self.booked_pieces:
            raise ValidationError("Collected pieces cannot exceed booked pieces.")

    # def save(self, *args, **kwargs):
    #     self.full_clean()
    #     super().save(*args, **kwargs)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.start_date} ({self.status})"


class BatchVariantConfig(models.Model):
    """
    Controls which box sizes (variants) are available for a specific batch.
    Created automatically (one row per active variant) when a batch is saved.
    The owner can flip is_enabled to hide a box size from the shop for this batch only.
    """
    batch_stock = models.ForeignKey(
        BatchStock,
        on_delete=models.CASCADE,
        related_name='variant_configs'
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.CASCADE,
        related_name='batch_configs'
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Owner toggle — set False to hide this box size from /shop for this batch"
    )
    custom_price = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Override the variant's default price for this batch only. Null = use variant.price."
    )

    class Meta:
        unique_together = ['batch_stock', 'variant']

    def effective_price(self):
        """Returns custom_price if set, otherwise falls back to variant.price."""
        return self.custom_price if self.custom_price is not None else self.variant.price

    def __str__(self):
        return (
            f"{self.batch_stock.product.name} - "
            f"{self.variant.label} "
            f"({'enabled' if self.is_enabled else 'disabled'})"
        )


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

    # Which box size was ordered
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
        help_text="Which box size was ordered"
    )
    # Immutable snapshot: quantity × variant.pieces at booking creation time.
    # Never recompute this after creation — it is historical record.
    pieces_used = models.PositiveIntegerField(
        default=0,
        help_text="Snapshot: quantity × variant.pieces at booking time."
    )

    pickup_date = models.DateField()
    quantity = models.PositiveIntegerField()

    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES, default='unpaid'
    )

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
                old_pieces_used = old_booking.pieces_used
            else:
                old_status = None
                old_pieces_used = 0

            # --------------------------------------------------
            # 1. COMPUTE pieces_used (only on creation)
            # --------------------------------------------------
            if is_new:
                if self.variant:
                    self.pieces_used = self.quantity * self.variant.pieces
                else:
                    # Fallback: treat each unit as 1 piece when no variant set
                    self.pieces_used = self.quantity

            # --------------------------------------------------
            # 2. DETERMINE PIECE RESERVATION CHANGE
            # --------------------------------------------------
            pieces_difference = 0

            if is_new:
                pieces_difference = self.pieces_used
            elif old_status != 'cancelled' and self.status == 'cancelled':
                # Cancellation — release pieces back to available
                pieces_difference = -old_pieces_used
            elif old_status == 'cancelled' and self.status != 'cancelled':
                # Un-cancellation — re-reserve pieces
                pieces_difference = self.pieces_used
            else:
                pieces_difference = 0  # quantity editing not allowed

            # Validate enough pieces are available
            if pieces_difference > 0:
                if pieces_difference > stock.available_pieces:
                    raise ValidationError(
                        f"Only {stock.available_pieces} pieces available in this batch."
                    )

            # --------------------------------------------------
            # 3. CALCULATE TOTAL AMOUNT
            #    Use variant's effective price (from BatchVariantConfig
            #    or variant.price directly). Fall back to product base_price
            #    for legacy bookings without a variant.
            # --------------------------------------------------
            if self.variant:
                try:
                    config = BatchVariantConfig.objects.get(
                        batch_stock=stock, variant=self.variant
                    )
                    unit_price = config.effective_price()
                except BatchVariantConfig.DoesNotExist:
                    unit_price = self.variant.price
            else:
                unit_price = stock.product.base_price

            base_total = self.quantity * unit_price

            if self.discount < 0:
                raise ValidationError("Discount cannot be negative.")
            if self.discount > base_total:
                raise ValidationError("Discount cannot exceed total amount.")

            self.total_amount = base_total - self.discount

            super().save(*args, **kwargs)

            # --------------------------------------------------
            # 4. ATOMICALLY UPDATE booked_pieces
            # --------------------------------------------------
            if pieces_difference != 0:
                BatchStock.objects.filter(pk=stock.pk).update(
                    booked_pieces=F('booked_pieces') + pieces_difference
                )

            # --------------------------------------------------
            # 5. ATOMICALLY UPDATE collected_pieces ON STATUS CHANGE
            # --------------------------------------------------
            collected_difference = 0

            if old_status != 'collected' and self.status == 'collected':
                collected_difference = self.pieces_used
            elif old_status == 'collected' and self.status != 'collected':
                collected_difference = -old_pieces_used

            if collected_difference != 0:
                BatchStock.objects.filter(pk=stock.pk).update(
                    collected_pieces=F('collected_pieces') + collected_difference
                )

    def __str__(self):
        return f"Booking {self.id} - {self.customer.name}"


# ------------------------------------------------------------------
# Signal: auto-create BatchVariantConfig rows when a batch is created
# ------------------------------------------------------------------

@receiver(post_save, sender=BatchStock)
def create_variant_configs_on_batch_create(sender, instance, created, **kwargs):
    """
    When a new BatchStock is first saved, automatically create one
    BatchVariantConfig row for every active variant on the product.
    All configs start as is_enabled=True — owner can disable per batch.
    """
    if not created:
        return

    active_variants = instance.product.variants.filter(is_active=True)
    BatchVariantConfig.objects.bulk_create([
        BatchVariantConfig(
            batch_stock=instance,
            variant=variant,
            is_enabled=True
        )
        for variant in active_variants
    ])