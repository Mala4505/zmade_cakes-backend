from rest_framework import serializers
from .models import Order, OrderStatusHistory, CollateralItem, Invoice, ORDER_STATUS_CHOICES


class OrderSerializer(serializers.ModelSerializer):
    collateral_items = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    def get_total(self, obj):
        return str(obj.total)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "customer_name",
            "phone",
            "email",
            "area",
            "address",
            "pickup_or_delivery",
            "items",
            "delivery_date",
            "delivery_time",
            "status",
            "payment_status",
            "payment_date",
            "is_locked",
            "edit_token",
            "invoice_token",
            "admin_notes",
            "customer_notes",
            "created_at",
            "updated_at",
            "collateral_items",
            "total",
        ]
        read_only_fields = ["order_number", "edit_token", "invoice_token", "created_at", "updated_at", "total"]

    def get_collateral_items(self, obj):
        return [
            {
                "item_name": c.item_name,
                "deposit_amount": str(c.deposit_amount),
                "return_required": c.return_required,
            }
            for c in obj.collateral_items.all()
        ]


class CollateralItemWriteSerializer(serializers.Serializer):
    item_name = serializers.CharField()
    deposit_amount = serializers.DecimalField(max_digits=10, decimal_places=3, default=0)
    return_required = serializers.BooleanField(default=True)


class OrderCreateUpdateSerializer(serializers.ModelSerializer):
    collateral_items = CollateralItemWriteSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = Order
        fields = [
            "customer_name",
            "phone",
            "email",
            "area",
            "address",
            "pickup_or_delivery",
            "items",
            "delivery_date",
            "delivery_time",
            "status",
            "admin_notes",
            "customer_notes",
            "collateral_items",
        ]

    def create(self, validated_data):
        collateral_data = validated_data.pop("collateral_items", [])
        order = Order.objects.create(**validated_data)
        for item in collateral_data:
            CollateralItem.objects.create(order=order, item_name=item["item_name"], deposit_amount=item.get("deposit_amount", 0), return_required=item.get("return_required", True))
        return order

    def update(self, instance, validated_data):
        collateral_data = validated_data.pop("collateral_items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if collateral_data is not None:
            instance.collateral_items.all().delete()
            for item in collateral_data:
                CollateralItem.objects.create(order=instance, item_name=item["item_name"], deposit_amount=item.get("deposit_amount", 0), return_required=item.get("return_required", True))
        return instance


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[c[0] for c in ORDER_STATUS_CHOICES])


class OrderPaymentUpdateSerializer(serializers.Serializer):
    payment_status = serializers.ChoiceField(choices=["unpaid", "paid"])
