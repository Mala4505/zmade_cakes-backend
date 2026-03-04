from rest_framework import serializers
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = '__all__'

    def create(self, validated_data):
        phone = validated_data.get("phone")

        customer, created = Customer.objects.get_or_create(
            phone=phone,
            defaults={"name": validated_data.get("name")}
        )

        return customer