from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from decimal import Decimal
import datetime
import logging

from .models import BatchStock, BatchBooking, BatchVariantConfig
from .serializers import (
    BatchStockSerializer,
    BatchBookingSerializer,
    BatchVariantConfigSerializer,
    PublicBatchSerializer,
)

logger = logging.getLogger(__name__)


class BatchStockViewSet(viewsets.ModelViewSet):
    serializer_class = BatchStockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            BatchStock.objects
            .select_related('product')
            .prefetch_related('variant_configs__variant', 'product__variants')
            .all()
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    # ------------------------------------------------------------------
    # GET /api/batch/stocks/<id>/variant-configs/
    # ------------------------------------------------------------------
    @action(detail=True, methods=['get'], url_path='variant-configs')
    def variant_configs(self, request, pk=None):
        """List all variant configs for this batch."""
        batch = self.get_object()
        configs = batch.variant_configs.select_related('variant')
        serializer = BatchVariantConfigSerializer(configs, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # PATCH /api/batch/stocks/<id>/variant-configs/<config_pk>/
    # ------------------------------------------------------------------
    @action(
        detail=True,
        methods=['patch'],
        url_path=r'variant-configs/(?P<config_pk>[^/.]+)'
    )
    def update_variant_config(self, request, pk=None, config_pk=None):
        """Owner toggle: enable/disable a box size or set a custom price for this batch."""
        batch = self.get_object()
        config = get_object_or_404(BatchVariantConfig, pk=config_pk, batch_stock=batch)
        serializer = BatchVariantConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # GET /api/batch/stocks/dashboard-stats/
    # ------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """Aggregate KPIs for the admin dashboard — all data is real-time."""

        open_batches = BatchStock.objects.filter(status='open').count()

        # Piece-based stock totals (open batches only)
        stock_stats = BatchStock.objects.filter(status='open').aggregate(
            total=Sum('total_pieces'),
            booked=Sum('booked_pieces'),
            collected=Sum('collected_pieces'),
        )
        total = stock_stats['total'] or 0
        booked = stock_stats['booked'] or 0
        collected = stock_stats['collected'] or 0

        # Revenue: collected + paid
        revenue_collected = (
            BatchBooking.objects
            .filter(status='collected', payment_status='paid')
            .aggregate(t=Sum('total_amount'))['t']
            or Decimal('0')
        )

        # Revenue: unpaid bookings still active
        revenue_pending = (
            BatchBooking.objects
            .filter(payment_status='unpaid', status__in=['booked', 'collected'])
            .aggregate(t=Sum('total_amount'))['t']
            or Decimal('0')
        )

        # Monthly bookings for bar chart — last 6 months
        six_months_ago = timezone.now() - datetime.timedelta(days=180)
        monthly_data = (
            BatchBooking.objects
            .filter(created_at__gte=six_months_ago)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'), revenue=Sum('total_amount'))
            .order_by('month')
        )
        monthly_bookings = [
            {
                'month': entry['month'].strftime('%b %Y'),
                'bookings': entry['count'],
                'revenue': float(entry['revenue'] or 0),
            }
            for entry in monthly_data
        ]

        # Per-product breakdown for pie/donut chart
        product_breakdown = list(
            BatchBooking.objects
            .filter(status__in=['booked', 'collected'])
            .values('batch_stock__product__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        product_breakdown_data = [
            {
                'product': e['batch_stock__product__name'],
                'count': e['count'],
            }
            for e in product_breakdown
        ]

        return Response({
            'open_batches': open_batches,
            'total_available': total - booked,
            'total_booked': booked,
            'total_collected': collected,
            'revenue_collected': float(revenue_collected),
            'revenue_pending': float(revenue_pending),
            'monthly_bookings': monthly_bookings,
            'product_breakdown': product_breakdown_data,
        })

    # Keep the old alias so any existing frontend calls don't break
    @action(detail=False, methods=['get'], url_path='stats/dashboard')
    def stats_dashboard(self, request):
        return self.dashboard_stats(request)


class BatchBookingViewSet(viewsets.ModelViewSet):
    serializer_class = BatchBookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = (
            BatchBooking.objects
            .select_related('customer', 'batch_stock__product', 'variant')
            .all()
        )

        params = self.request.query_params
        if params.get('customer'):
            queryset = queryset.filter(customer_id=params['customer'])
        if params.get('batch_stock'):
            queryset = queryset.filter(batch_stock_id=params['batch_stock'])
        if params.get('payment_status'):
            queryset = queryset.filter(payment_status=params['payment_status'])
        if params.get('status'):
            queryset = queryset.filter(status=params['status'])

        return queryset.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """Wrap creation so any unexpected error returns a 400 instead of a raw 500."""
        try:
            return super().create(request, *args, **kwargs)
        except Exception as exc:
            logger.error("Booking creation failed: %s", exc, exc_info=True)
            return Response(
                {'detail': 'Booking could not be created. Please check your details and try again.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def partial_update(self, request, *args, **kwargs):
        """
        On status change, update booked_pieces / collected_pieces atomically.
        The model's save() handles this too, but doing it here via F() expressions
        is the safe race-condition-free path for API-driven status changes.
        """
        booking = self.get_object()
        new_status = request.data.get('status')

        if new_status and new_status != booking.status:
            if new_status == 'collected' and booking.status == 'booked':
                BatchStock.objects.filter(pk=booking.batch_stock_id).update(
                    collected_pieces=F('collected_pieces') + booking.pieces_used
                )
            elif new_status == 'cancelled' and booking.status == 'booked':
                BatchStock.objects.filter(pk=booking.batch_stock_id).update(
                    booked_pieces=F('booked_pieces') - booking.pieces_used
                )

        return super().partial_update(request, *args, **kwargs)


class PublicBatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public endpoint — no authentication required.
    Used by /shop to display available products and box sizes.
    Returns ALL open batches regardless of product.active.
    The frontend is responsible for visually disabling inactive products.
    """
    permission_classes = [AllowAny]
    serializer_class = PublicBatchSerializer

    def get_queryset(self):
        # Intentionally NO product__active filter — shop shows all, disables inactive visually
        return (
            BatchStock.objects
            .filter(status='open')
            .select_related('product')
            .prefetch_related('variant_configs__variant', 'product__variants')
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context