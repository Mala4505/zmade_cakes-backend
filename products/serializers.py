from rest_framework import serializers
from .models import Product, ProductVariant


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'pieces', 'label', 'price', 'is_active', 'sort_order']


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'type', 'base_price', 'flavor', 'active',
            'description', 'image', 'image_url',
            'variants', 'created_at', 'updated_at'
        ]

    def get_image_url(self, obj):
        # Prefer uploaded image, fall back to stored URL field
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return obj.image_url or None