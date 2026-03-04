from django.db import models
from django.core.exceptions import ValidationError


class Customer(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    phone = models.CharField(max_length=20, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        # Must contain digits only
        if not self.phone.isdigit():
            raise ValidationError("Phone number must contain digits only.")

        # Kuwait number (8 digits)
        if len(self.phone) == 8:
            return

        # International number (must start with 00)
        if self.phone.startswith("00") and len(self.phone) >= 10:
            return

        raise ValidationError(
            "Enter a valid Kuwait number (8 digits) or international number starting with 00."
        )

    def save(self, *args, **kwargs):
        self.full_clean()  # ensures validation runs always
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.phone})"