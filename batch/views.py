from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import BatchStock, BatchBooking
from .serializers import BatchStockSerializer, BatchBookingSerializer


class BatchStockViewSet(viewsets.ModelViewSet):
    queryset = BatchStock.objects.all()
    serializer_class = BatchStockSerializer
    permission_classes = [IsAuthenticated]


class BatchBookingViewSet(viewsets.ModelViewSet):
    serializer_class = BatchBookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = BatchBooking.objects.all()

        customer = self.request.query_params.get('customer')
        payment_status = self.request.query_params.get('payment_status')
        status = self.request.query_params.get('status')

        if customer:
            queryset = queryset.filter(customer_id=customer)

        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)

        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at')