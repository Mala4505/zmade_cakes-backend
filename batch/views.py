from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q, F
from decimal import Decimal

from .models import BatchStock, BatchBooking
from .serializers import BatchStockSerializer, BatchBookingSerializer


class BatchStockViewSet(viewsets.ModelViewSet):
    queryset = BatchStock.objects.all().select_related('product')
    serializer_class = BatchStockSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """
        Aggregate statistics for dashboard KPI cards.
        """
        # Open batches count
        open_batches = BatchStock.objects.filter(status='open').count()

        # Stock statistics
        stock_stats = BatchStock.objects.filter(status='open').aggregate(
            total_quantity=Sum('total_quantity'),
            booked_quantity=Sum('booked_quantity'),
            collected_quantity=Sum('collected_quantity')
        )

        total_qty = stock_stats['total_quantity'] or 0
        booked_qty = stock_stats['booked_quantity'] or 0
        collected_qty = stock_stats['collected_quantity'] or 0

        # Revenue calculations
        # Collected revenue: paid AND collected
        revenue_collected = BatchBooking.objects.filter(
            status='collected',
            payment_status='paid'
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')

        # Pending revenue: unpaid bookings that are booked or collected
        revenue_pending = BatchBooking.objects.filter(
            payment_status='unpaid',
            status__in=['booked', 'collected']
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')

        return Response({
            'open_batches': open_batches,
            'total_available': total_qty - booked_qty,
            'total_booked': booked_qty,
            'total_collected': collected_qty,
            'revenue_collected': float(revenue_collected),
            'revenue_pending': float(revenue_pending),
        })

    @action(detail=False, methods=['get'], url_path='stats/dashboard')
    def stats_dashboard(self, request):
        """
        Alternative URL for dashboard stats (matches frontend API expectation).
        """
        return self.dashboard_stats(request)


class BatchBookingViewSet(viewsets.ModelViewSet):
    serializer_class = BatchBookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = BatchBooking.objects.all().select_related('customer', 'batch_stock__product')

        # Filter by query params
        customer = self.request.query_params.get('customer')
        batch_stock = self.request.query_params.get('batch_stock')
        payment_status = self.request.query_params.get('payment_status')
        status = self.request.query_params.get('status')

        if customer:
            queryset = queryset.filter(customer_id=customer)
        if batch_stock:
            queryset = queryset.filter(batch_stock_id=batch_stock)
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at')
