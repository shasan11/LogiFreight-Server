# purchase/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated

from .models import (
    VendorBillsGroup, ExpenseCategory, Expenses, ExpensesItems,
    VendorBills, VendorBillItems,
    VendorPayments, VendorPaymentEntries,
)
from .serializers import (
    VendorBillsGroupSerializer, ExpenseCategorySerializer,
    ExpensesSerializer, ExpensesItemsSerializer,
    VendorBillsSerializer, VendorBillItemsSerializer,
    VendorPaymentsSerializer, VendorPaymentEntriesSerializer,
)
from .filters import (
    VendorBillsGroupFilter, ExpenseCategoryFilter,
    ExpensesFilter, ExpensesItemsFilter,
    VendorBillsFilter, VendorBillItemsFilter,
    VendorPaymentsFilter, VendorPaymentEntriesFilter,
)


class BaseModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]


class VendorBillsGroupViewSet(BaseModelViewSet):
    queryset = VendorBillsGroup.objects.all()
    serializer_class = VendorBillsGroupSerializer
    filterset_class = VendorBillsGroupFilter
    search_fields = ["no", "status"]
    ordering_fields = ["created", "id"]


class ExpenseCategoryViewSet(BaseModelViewSet):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    filterset_class = ExpenseCategoryFilter
    search_fields = ["name"]
    ordering_fields = ["name", "created", "id"]


# --------------------------
# EXPENSES + ITEMS (nested via @action)
# --------------------------
class ExpensesViewSet(BaseModelViewSet):
    queryset = Expenses.objects.all().select_related("supplier", "currency", "expense_category", "branch").prefetch_related("expenses_items")
    serializer_class = ExpensesSerializer
    filterset_class = ExpensesFilter
    search_fields = ["exp_no", "invoice_reference"]
    ordering_fields = ["date", "due_date", "created", "id"]

    @action(detail=True, methods=["get", "post"], url_path="items")
    def items(self, request, pk=None):
        expense = self.get_object()

        if request.method == "GET":
            qs = expense.expenses_items.all()
            ser = ExpensesItemsSerializer(qs, many=True)
            return Response(ser.data)

        ser = ExpensesItemsSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(expenses=expense)  # triggers model save -> recalcs
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "patch", "delete"], url_path=r"items/(?P<item_id>[^/.]+)")
    def item_detail(self, request, pk=None, item_id=None):
        expense = self.get_object()
        item = get_object_or_404(ExpensesItems, id=item_id, expenses=expense)

        if request.method == "GET":
            return Response(ExpensesItemsSerializer(item).data)

        if request.method == "PATCH":
            ser = ExpensesItemsSerializer(item, data=request.data, partial=True)
            ser.is_valid(raise_exception=True)
            ser.save()  # triggers recalcs
            return Response(ser.data)

        item.delete()  # triggers recalcs via model delete override
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExpensesItemsViewSet(BaseModelViewSet):
    queryset = ExpensesItems.objects.all().select_related("expenses")
    serializer_class = ExpensesItemsSerializer
    filterset_class = ExpensesItemsFilter
    ordering_fields = ["id"]


# --------------------------
# VENDOR BILLS + ITEMS
# --------------------------
class VendorBillsViewSet(BaseModelViewSet):
    queryset = VendorBills.objects.all().select_related("vendor", "currency", "vendor_bills_group", "branch").prefetch_related("bill_items")
    serializer_class = VendorBillsSerializer
    filterset_class = VendorBillsFilter
    search_fields = ["no", "invoice_reference"]
    ordering_fields = ["date", "due_date", "created", "id"]

    @action(detail=True, methods=["get", "post"], url_path="items")
    def items(self, request, pk=None):
        bill = self.get_object()

        if request.method == "GET":
            ser = VendorBillItemsSerializer(bill.bill_items.all(), many=True)
            return Response(ser.data)

        ser = VendorBillItemsSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(vendorbills=bill)  # triggers recalcs
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "patch", "delete"], url_path=r"items/(?P<item_id>[^/.]+)")
    def item_detail(self, request, pk=None, item_id=None):
        bill = self.get_object()
        item = get_object_or_404(VendorBillItems, id=item_id, vendorbills=bill)

        if request.method == "GET":
            return Response(VendorBillItemsSerializer(item).data)

        if request.method == "PATCH":
            ser = VendorBillItemsSerializer(item, data=request.data, partial=True)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(ser.data)

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VendorBillItemsViewSet(BaseModelViewSet):
    queryset = VendorBillItems.objects.all().select_related("vendorbills", "branch")
    serializer_class = VendorBillItemsSerializer
    filterset_class = VendorBillItemsFilter
    ordering_fields = ["id"]


# --------------------------
# VENDOR PAYMENTS + ENTRIES
# --------------------------
class VendorPaymentsViewSet(BaseModelViewSet):
    queryset = VendorPayments.objects.all().select_related("vendor", "currency", "branch").prefetch_related("payment_entries")
    serializer_class = VendorPaymentsSerializer
    filterset_class = VendorPaymentsFilter
    search_fields = ["no", "remarks"]
    ordering_fields = ["date", "created", "id"]

    @action(detail=True, methods=["get", "post"], url_path="entries")
    def entries(self, request, pk=None):
        pay = self.get_object()

        if request.method == "GET":
            ser = VendorPaymentEntriesSerializer(pay.payment_entries.all(), many=True)
            return Response(ser.data)

        ser = VendorPaymentEntriesSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(vendor_payments=pay)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "patch", "delete"], url_path=r"entries/(?P<entry_id>[^/.]+)")
    def entry_detail(self, request, pk=None, entry_id=None):
        pay = self.get_object()
        entry = get_object_or_404(VendorPaymentEntries, id=entry_id, vendor_payments=pay)

        if request.method == "GET":
            return Response(VendorPaymentEntriesSerializer(entry).data)

        if request.method == "PATCH":
            ser = VendorPaymentEntriesSerializer(entry, data=request.data, partial=True)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(ser.data)

        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VendorPaymentEntriesViewSet(BaseModelViewSet):
    queryset = VendorPaymentEntries.objects.all().select_related("vendor_payments", "vendor_bills", "branch")
    serializer_class = VendorPaymentEntriesSerializer
    filterset_class = VendorPaymentEntriesFilter
    ordering_fields = ["id"]
