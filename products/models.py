# from django.db import models
# from django.core.exceptions import ValidationError


# class Product(models.Model):
#     TYPE_CHOICES = (
#         ('custom', 'Custom'),
#         ('batch', 'Batch'),
#     )

#     name = models.CharField(max_length=255)
#     type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)

#     base_price = models.DecimalField(max_digits=10, decimal_places=3)
#     flavor = models.CharField(max_length=255, blank=True)

#     description = models.TextField(blank=True, default='')

#     # URL-based image fallback (kept for backward compat)
#     image_url = models.URLField(max_length=500, blank=True, default='')

#     # Uploaded image (preferred — requires Pillow)
#     image = models.ImageField(
#         upload_to='products/',
#         null=True,
#         blank=True,
#         help_text="Product display image shown in the shop and admin"
#     )

#     active = models.BooleanField(default=True)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ['name']

#     def clean(self):
#         if self.base_price < 0:
#             raise ValidationError("Base price cannot be negative.")

#     def save(self, *args, **kwargs):
#         self.full_clean()
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.name} ({self.get_type_display()})"


# class ProductVariant(models.Model):
#     """
#     A single box size option for a product.
#     e.g. Brownies can have variants: 3pc box, 6pc box, 12pc box.
#     Each variant has its own piece count, display label, and price.
#     """
#     product = models.ForeignKey(
#         Product,
#         on_delete=models.CASCADE,
#         related_name='variants'
#     )
#     pieces = models.PositiveIntegerField(
#         help_text="Number of pieces in this box size, e.g. 3, 6, 12"
#     )
#     label = models.CharField(
#         max_length=50,
#         help_text="Display label shown to customers, e.g. '12 pcs box'"
#     )
#     price = models.DecimalField(
#         max_digits=8,
#         decimal_places=3,
#         help_text="Price for this box size in KD"
#     )
#     is_active = models.BooleanField(
#         default=True,
#         help_text="Global toggle — if False, this variant is hidden from all batches and the shop"
#     )
#     sort_order = models.PositiveIntegerField(
#         default=0,
#         help_text="Display order in the shop, lowest value shown first"
#     )

#     class Meta:
#         ordering = ['sort_order', 'pieces']
#         unique_together = ['product', 'pieces']

#     def __str__(self):
#         return f"{self.product.name} — {self.label}"

from django.db import models
from django.core.exceptions import ValidationError


class Product(models.Model):
    TYPE_CHOICES = (
        ('custom', 'Custom'),
        ('batch', 'Batch'),
    )

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=3)
    flavor = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, default='')

    # URL-based image fallback (kept for backward compat)
    image_url = models.URLField(max_length=500, blank=True, default='')

    # Uploaded image — requires Pillow
    image = models.ImageField(
        upload_to='products/',
        null=True,
        blank=True,
        help_text="Product display image shown in the shop and admin"
    )

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class ProductVariant(models.Model):
    """
    A single box size option for a product.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    pieces = models.PositiveIntegerField(
        help_text="Number of pieces in this box size, e.g. 3, 6, 12"
    )
    label = models.CharField(
        max_length=50,
        help_text="Display label shown to customers, e.g. '12 pcs box'"
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        help_text="Price for this box size in KD"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Global toggle — if False, hidden from all batches and the shop"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order in the shop, lowest value shown first"
    )

    class Meta:
        ordering = ['sort_order', 'pieces']
        unique_together = ['product', 'pieces']

    def __str__(self):
        return f"{self.product.name} — {self.label}"