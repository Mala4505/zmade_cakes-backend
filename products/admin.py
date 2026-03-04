from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'base_price', 'active', 'created_at')
    list_filter = ('type', 'active')
    search_fields = ('name', 'flavor')
    readonly_fields = ('created_at', 'updated_at')