from rest_framework import serializers
from decimal import Decimal

from .models import BatchStock, BatchBooking, BatchVariantConfig
from products.models import Product, ProductVariant
from products.serializers import ProductSerializer, ProductVariantSerializer
from customers.models import Customer


# Minimal customer serializer used inside booking responses
class _CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone']


# ─────────────────────────────────────────────
# BatchVariantConfig
# ─────────────────────────────────────────────

class BatchVariantConfigSerializer(serializers.ModelSerializer):
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),
        source='variant',
        write_only=True
    )
    effective_price = serializers.SerializerMethodField()

    class Meta:
        model = BatchVariantConfig
        fields = ['id', 'variant', 'variant_id', 'is_enabled', 'custom_price', 'effective_price']

    def get_effective_price(self, obj):
        return str(obj.effective_price())


# ─────────────────────────────────────────────
# BatchStock
# ─────────────────────────────────────────────

class BatchStockSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    variant_configs = BatchVariantConfigSerializer(many=True, read_only=True)
    available_pieces = serializers.ReadOnlyField()

    class Meta:
        model = BatchStock
        fields = [
            'id', 'product', 'product_id', 'start_date',
            'total_pieces', 'booked_pieces', 'collected_pieces', 'available_pieces',
            'status', 'variant_configs', 'created_at'
        ]


# ─────────────────────────────────────────────
# BatchBooking
# ─────────────────────────────────────────────

class BatchBookingSerializer(serializers.ModelSerializer):
    customer = _CustomerSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source='customer',
        write_only=True
    )
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),
        source='variant',
        write_only=True,
        required=False,
        allow_null=True
    )
    # total_amount is editable=False on the model — DRF makes it read-only automatically
    # pieces_used is also set by the model, expose as read-only
    pieces_used = serializers.IntegerField(read_only=True)

    class Meta:
        model = BatchBooking
        fields = [
            'id',
            'customer', 'customer_id',
            'batch_stock',
            'variant', 'variant_id',
            'quantity', 'pieces_used',
            'pickup_date',
            'payment_method', 'payment_status',
            'discount', 'total_amount',
            'status',
            'created_at',
        ]
        read_only_fields = ['total_amount', 'pieces_used']

    def validate(self, data):
        instance = self.instance

        batch_stock = data.get('batch_stock', getattr(instance, 'batch_stock', None))
        pickup_date = data.get('pickup_date', getattr(instance, 'pickup_date', None))
        quantity = data.get('quantity', getattr(instance, 'quantity', 1))
        status = data.get('status', getattr(instance, 'status', 'booked'))
        variant = data.get('variant', getattr(instance, 'variant', None))

        # Pickup date must fall within the batch window
        if pickup_date and batch_stock:
            if pickup_date < batch_stock.start_date:
                raise serializers.ValidationError({
                    'pickup_date': 'Pickup date cannot be before batch start date.'
                })

        # Only run availability checks on new bookings that aren't being cancelled
        if not instance and status != 'cancelled' and batch_stock:
            if batch_stock.status != 'open':
                raise serializers.ValidationError({
                    'batch_stock': 'This batch is closed.'
                })

            if variant:
                if not variant.is_active:
                    raise serializers.ValidationError({
                        'variant': 'This box size is not currently active.'
                    })

                try:
                    config = BatchVariantConfig.objects.get(
                        batch_stock=batch_stock, variant=variant
                    )
                    if not config.is_enabled:
                        raise serializers.ValidationError({
                            'variant': 'This box size is not enabled for this batch.'
                        })
                except BatchVariantConfig.DoesNotExist:
                    raise serializers.ValidationError({
                        'variant': 'This box size is not configured for this batch.'
                    })

                pieces_needed = variant.pieces * quantity
                if pieces_needed > batch_stock.available_pieces:
                    raise serializers.ValidationError({
                        'quantity': (
                            f'Not enough pieces available. '
                            f'Need {pieces_needed}, have {batch_stock.available_pieces}.'
                        )
                    })
            else:
                # Legacy path — no variant, check old available_quantity
                if quantity > batch_stock.available_quantity:
                    raise serializers.ValidationError({
                        'quantity': f'Only {batch_stock.available_quantity} items available.'
                    })

        return data


# ─────────────────────────────────────────────
# Public shop serializers — no auth required
# ─────────────────────────────────────────────

class PublicVariantOptionSerializer(serializers.Serializer):
    """Flattened variant + config for the /shop UI. No sensitive info exposed."""
    variant_id = serializers.IntegerField(source='variant.id')
    pieces = serializers.IntegerField(source='variant.pieces')
    label = serializers.CharField(source='variant.label')
    price = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    is_enabled = serializers.BooleanField()

    def get_price(self, obj):
        return str(obj.effective_price())

    def get_is_available(self, obj):
        batch = self.context.get('batch')
        if not batch:
            return False
        return (
            obj.is_enabled
            and obj.variant.is_active
            and batch.available_pieces >= obj.variant.pieces
        )


class PublicBatchSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for the public /shop endpoint.
    Shows all open batches regardless of product.active — frontend handles
    visual disabling of inactive products.
    """
    product_id = serializers.IntegerField(source='product.id')
    product_name = serializers.CharField(source='product.name')
    product_flavor = serializers.CharField(source='product.flavor')
    product_image = serializers.SerializerMethodField()
    product_active = serializers.BooleanField(source='product.active')
    available_pieces = serializers.ReadOnlyField()
    variants = serializers.SerializerMethodField()

    class Meta:
        model = BatchStock
        fields = [
            'id',
            'product_id', 'product_name', 'product_flavor',
            'product_image', 'product_active',
            'start_date', 'available_pieces',
            'variants',
        ]

    def get_product_image(self, obj):
        if obj.product.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.product.image.url)
            return obj.product.image.url
        return obj.product.image_url or None

    def get_variants(self, batch):
        configs = (
            batch.variant_configs
            .select_related('variant')
            .filter(variant__is_active=True)
            .order_by('variant__sort_order', 'variant__pieces')
        )
        return PublicVariantOptionSerializer(
            configs, many=True, context={'batch': batch, 'request': self.context.get('request')}
        ).data