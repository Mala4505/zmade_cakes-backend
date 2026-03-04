from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Product.objects.all()

        product_type = self.request.query_params.get('type')
        active = self.request.query_params.get('active')

        if product_type:
            queryset = queryset.filter(type=product_type)

        if active is not None:
            queryset = queryset.filter(active=active.lower() == 'true')

        return queryset.order_by('-created_at')