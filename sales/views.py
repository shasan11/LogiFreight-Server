from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Sales, SalesItem, CustomerPayment, CustomerPaymentItems
from .serializers import (
    SalesSerializer,
    SalesItemSerializer,
    CustomerPaymentSerializer,
    CustomerPaymentItemsSerializer,
)
from .filters import (
    SalesFilter,
    SalesItemFilter,
    CustomerPaymentFilter,
    CustomerPaymentItemsFilter,
)


class BaseModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]


class SalesViewSet(BaseModelViewSet):
    queryset = Sales.objects.all().select_related("customer", "currency", "shipment", "branch").prefetch_related("items")
    serializer_class = SalesSerializer
    filterset_class = SalesFilter
    search_fields = ["no", "reference", "po_number"]
    ordering_fields = ["invoice_date", "created", "id", "no", "total", "paid_amount", "balance_due"]

    @action(detail=True, methods=["get", "post"], url_path="items")
    def items(self, request, pk=None):
        sale = self.get_object()

        if request.method == "GET":
            serializer = SalesItemSerializer(sale.items.all(), many=True)
            return Response(serializer.data)

        serializer = SalesItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(sales=sale, branch=sale.branch)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "patch", "delete"], url_path=r"items/(?P<item_id>[^/.]+)")
    def item_detail(self, request, pk=None, item_id=None):
        sale = self.get_object()
        item = get_object_or_404(SalesItem, id=item_id, sales=sale)

        if request.method == "GET":
            return Response(SalesItemSerializer(item).data)

        if request.method == "PATCH":
            serializer = SalesItemSerializer(item, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SalesItemViewSet(BaseModelViewSet):
    queryset = SalesItem.objects.all().select_related("sales", "branch")
    serializer_class = SalesItemSerializer
    filterset_class = SalesItemFilter
    ordering_fields = ["id", "created", "updated"]


class CustomerPaymentViewSet(BaseModelViewSet):
    queryset = CustomerPayment.objects.all().select_related(
        "customer", "currency", "bank_account", "cheque_register", "branch"
    ).prefetch_related("allocations")
    serializer_class = CustomerPaymentSerializer
    filterset_class = CustomerPaymentFilter
    search_fields = ["no", "payment_reference_number", "desc"]
    ordering_fields = ["date", "created", "id", "no", "amount"]

    @action(detail=True, methods=["get", "post"], url_path="allocations")
    def allocations(self, request, pk=None):
        payment = self.get_object()

        if request.method == "GET":
            serializer = CustomerPaymentItemsSerializer(payment.allocations.all(), many=True)
            return Response(serializer.data)

        serializer = CustomerPaymentItemsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(customerpayment=payment, branch=payment.branch)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "patch", "delete"], url_path=r"allocations/(?P<allocation_id>[^/.]+)")
    def allocation_detail(self, request, pk=None, allocation_id=None):
        payment = self.get_object()
        allocation = get_object_or_404(CustomerPaymentItems, id=allocation_id, customerpayment=payment)

        if request.method == "GET":
            return Response(CustomerPaymentItemsSerializer(allocation).data)

        if request.method == "PATCH":
            serializer = CustomerPaymentItemsSerializer(allocation, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        allocation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomerPaymentItemsViewSet(BaseModelViewSet):
    queryset = CustomerPaymentItems.objects.all().select_related("customerpayment", "sales", "branch")
    serializer_class = CustomerPaymentItemsSerializer
    filterset_class = CustomerPaymentItemsFilter
    ordering_fields = ["id", "created", "updated"]
