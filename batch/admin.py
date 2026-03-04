from django.contrib import admin
from .models import BatchStock, BatchBooking


@admin.register(BatchStock)
class BatchStockAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'product',
        'start_date',
        'total_quantity',
        'booked_quantity',
        'available_quantity',
        'status'
    )
    list_filter = ('status', 'start_date')
    readonly_fields = ('available_quantity',)


@admin.register(BatchBooking)
class BatchBookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'batch_stock',
        'pickup_date',
        'quantity',
        'payment_status',
        'status'
    )
    list_filter = ('status', 'payment_status', 'payment_method')
    search_fields = ('customer__name', 'customer__phone')