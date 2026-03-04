from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BatchStockViewSet, BatchBookingViewSet

router = DefaultRouter()
router.register(r'stocks', BatchStockViewSet, basename='batchstock')
router.register(r'bookings', BatchBookingViewSet, basename='batchbooking')

urlpatterns = [
    path('', include(router.urls)),
]