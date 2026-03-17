from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BatchStockViewSet, BatchBookingViewSet, PublicBatchViewSet

router = DefaultRouter()
router.register(r'stocks', BatchStockViewSet, basename='batchstock')
router.register(r'bookings', BatchBookingViewSet, basename='batchbooking')
router.register(r'public', PublicBatchViewSet, basename='public-batch')

urlpatterns = [
    path('', include(router.urls)),
]