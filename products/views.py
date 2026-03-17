from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404

from .models import Product, ProductVariant
from .serializers import ProductSerializer, ProductVariantSerializer


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = Product.objects.prefetch_related('variants').all()

        product_type = self.request.query_params.get('type')
        active = self.request.query_params.get('active')

        if product_type:
            queryset = queryset.filter(type=product_type)

        if active is not None:
            queryset = queryset.filter(active=active.lower() == 'true')

        return queryset.order_by('-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    # ------------------------------------------------------------------
    # GET  /api/products/<id>/variants/       → list variants
    # POST /api/products/<id>/variants/       → create variant
    # ------------------------------------------------------------------
    @action(detail=True, methods=['get', 'post'], url_path='variants')
    def variants(self, request, pk=None):
        product = self.get_object()

        if request.method == 'GET':
            serializer = ProductVariantSerializer(
                product.variants.all(), many=True
            )
            return Response(serializer.data)

        # POST — create a new variant for this product
        serializer = ProductVariantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # PATCH  /api/products/<id>/variants/<variant_pk>/   → update variant
    # DELETE /api/products/<id>/variants/<variant_pk>/   → delete variant
    # ------------------------------------------------------------------
    @action(
        detail=True,
        methods=['patch', 'delete'],
        url_path=r'variants/(?P<variant_pk>[^/.]+)'
    )
    def variant_detail(self, request, pk=None, variant_pk=None):
        product = self.get_object()
        variant = get_object_or_404(ProductVariant, pk=variant_pk, product=product)

        if request.method == 'PATCH':
            serializer = ProductVariantSerializer(
                variant, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        # DELETE — block if any non-cancelled bookings reference this variant
        if variant.bookings.exclude(status='cancelled').exists():
            return Response(
                {'detail': 'Cannot delete a variant that has active bookings.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        variant.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)