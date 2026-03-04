from rest_framework import serializers
from .models import BatchStock, BatchBooking


class BatchStockSerializer(serializers.ModelSerializer):
    available_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = BatchStock
        fields = '__all__'


class BatchBookingSerializer(serializers.ModelSerializer):

    class Meta:
        model = BatchBooking
        fields = '__all__'

    def validate(self, data):
        instance = self.instance

        batch_stock = data.get('batch_stock', getattr(instance, 'batch_stock', None))
        pickup_date = data.get('pickup_date', getattr(instance, 'pickup_date', None))
        quantity = data.get('quantity', getattr(instance, 'quantity', None))
        status = data.get('status', getattr(instance, 'status', 'booked'))

        if pickup_date and batch_stock:
            if pickup_date < batch_stock.start_date:
                raise serializers.ValidationError({
                    'pickup_date': 'Pickup date cannot be before batch start date.'
                })

        if not instance and status != 'cancelled' and quantity and batch_stock:
            if quantity > batch_stock.available_quantity:
                raise serializers.ValidationError({
                    'quantity': f'Only {batch_stock.available_quantity} items available.'
                })

        return data