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
    flavor = models.CharField(max_length=255, blank=True)  # no null=True

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def clean(self):
        if self.base_price < 0:
            raise ValidationError("Base price cannot be negative.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"