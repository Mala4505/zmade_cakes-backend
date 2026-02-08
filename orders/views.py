from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Order
from .serializers import (
    OrderSerializer,
    OrderCreateUpdateSerializer,
    OrderStatusUpdateSerializer,
    OrderPaymentUpdateSerializer,
)


@api_view(["GET", "POST"])
def admin_order_list(request):
    if request.method == "GET":
        delivery_date = request.query_params.get("delivery_date")
        qs = Order.objects.all()
        if delivery_date:
            qs = qs.filter(delivery_date=delivery_date)
        serializer = OrderSerializer(qs, many=True)
        return Response(serializer.data)
    else:
        serializer = OrderCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def admin_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "GET":
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    elif request.method == "PUT":
        if order.is_locked:
            return Response(
                {"detail": "Order is locked and cannot be edited."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = OrderCreateUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data)
    else:
        if order.status != "draft":
            return Response(
                {"detail": "Only draft orders can be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def admin_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    serializer = OrderStatusUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    old_status = order.status
    order.status = serializer.validated_data["status"]
    order.save()
    from orders.signals import order_status_changed
    order_status_changed.send(sender=Order, instance=order, old_status=old_status, changed_by="admin")
    return Response(OrderSerializer(order).data)


@api_view(["POST"])
def admin_order_payment(request, pk):
    order = get_object_or_404(Order, pk=pk)
    serializer = OrderPaymentUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    from django.utils import timezone
    order.payment_status = serializer.validated_data["payment_status"]
    order.payment_date = timezone.now() if order.payment_status == "paid" else None
    order.save()
    from orders.signals import order_payment_changed
    order_payment_changed.send(sender=Order, instance=order, changed_by="admin")
    return Response(OrderSerializer(order).data)


@api_view(["GET", "PUT"])
def public_order_edit(request, token):
    order = get_object_or_404(Order, edit_token=token)
    if order.is_locked:
        return Response(
            {"detail": "Order is locked and cannot be edited."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if request.method == "GET":
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    else:
        serializer = OrderCreateUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        from orders.signals import order_edited_by_customer
        order_edited_by_customer.send(sender=Order, instance=order)
        return Response(OrderSerializer(order).data)


@api_view(["GET"])
def public_order_view(request, token):
    order = get_object_or_404(Order, invoice_token=token)
    serializer = OrderSerializer(order)
    return Response(serializer.data)
