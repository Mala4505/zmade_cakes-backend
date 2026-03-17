from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import BatchStock, BatchVariantConfig


@receiver(post_save, sender=BatchStock)
def create_variant_configs_on_batch_create(sender, instance, created, **kwargs):
    """
    When a new BatchStock is saved for the first time, automatically create
    a BatchVariantConfig row for each active variant on the product.
    All configs default to is_enabled=True.
    """
    if not created:
        return

    # Get all active variants for this product
    from products.models import ProductVariant
    active_variants = ProductVariant.objects.filter(
        product=instance.product,
        is_active=True
    )

    BatchVariantConfig.objects.bulk_create([
        BatchVariantConfig(
            batch_stock=instance,
            variant=variant,
            is_enabled=True
        )
        for variant in active_variants
    ])