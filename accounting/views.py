# api/views.py
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    ChartofAccounts,
    BankAccounts,
    Currency,
    PaymentMethod,
    GeneralLedger,
    JournalVoucher,
    JournalVoucherItems,
    ChequeRegister,
    CashTransfer,
    CashTransferItems,
)
from .serializers import (
    ChartofAccountsSerializer,
    BankAccountsSerializer,
    CurrencySerializer,
    PaymentMethodSerializer,
    GeneralLedgerSerializer,
    JournalVoucherSerializer,
    JournalVoucherItemsSerializer,
    ChequeRegisterSerializer,
    CashTransferSerializer,
    CashTransferItemsSerializer,
)
from .filters import (
    ChartofAccountsFilter,
    BankAccountsFilter,
    CurrencyFilter,
    PaymentMethodFilter,
    GeneralLedgerFilter,
    JournalVoucherFilter,
    JournalVoucherItemsFilter,
    ChequeRegisterFilter,
    CashTransferFilter,
    CashTransferItemsFilter,
)


class ChartofAccountsViewSet(viewsets.ModelViewSet):
    queryset = ChartofAccounts.objects.all()
    serializer_class = ChartofAccountsSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = ChartofAccountsFilter
    search_fields = ("code", "name", "description")
    ordering_fields = ("code", "name", "type", "id")
    ordering = ("code",)


class BankAccountsViewSet(viewsets.ModelViewSet):
    queryset = BankAccounts.objects.all()
    serializer_class = BankAccountsSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = BankAccountsFilter
    search_fields = ("name", "display_name", "code", "account_number")
    ordering_fields = ("name", "code", "acc_type", "type", "id")
    ordering = ("name",)


class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = CurrencyFilter
    search_fields = ("name", "symbol")
    ordering_fields = ("name", "symbol", "is_default", "id")
    ordering = ("name",)


class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = PaymentMethodFilter
    search_fields = ("name", "description")
    ordering_fields = ("name", "id")
    ordering = ("name",)


class GeneralLedgerViewSet(viewsets.ModelViewSet):
    queryset = GeneralLedger.objects.all()
    serializer_class = GeneralLedgerSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = GeneralLedgerFilter
    ordering_fields = ("posting_date", "id", "debit", "credit")
    ordering = ("-posting_date", "-id")


class JournalVoucherViewSet(viewsets.ModelViewSet):
    queryset = JournalVoucher.objects.all().prefetch_related("items")
    serializer_class = JournalVoucherSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = JournalVoucherFilter
    search_fields = ("jv_no", "description")
    ordering_fields = ("jv_date", "jv_no", "approved", "id")
    ordering = ("-jv_date", "-id")


class JournalVoucherItemsViewSet(viewsets.ModelViewSet):
    queryset = JournalVoucherItems.objects.all()
    serializer_class = JournalVoucherItemsSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = JournalVoucherItemsFilter
    ordering_fields = ("id", "debit", "credit")
    ordering = ("id",)


class ChequeRegisterViewSet(viewsets.ModelViewSet):
    queryset = ChequeRegister.objects.all()
    serializer_class = ChequeRegisterSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = ChequeRegisterFilter
    search_fields = ("cheque_no", "voided_reason")
    ordering_fields = ("issued_received_date", "cheque_date", "status", "approved", "id")
    ordering = ("-issued_received_date", "-id")


class CashTransferViewSet(viewsets.ModelViewSet):
    queryset = CashTransfer.objects.all().prefetch_related("items")
    serializer_class = CashTransferSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = CashTransferFilter
    search_fields = ("cash_transfer_no", "description")
    ordering_fields = ("ct_date", "cash_transfer_no", "approved", "id")
    ordering = ("-ct_date", "-id")


class CashTransferItemsViewSet(viewsets.ModelViewSet):
    queryset = CashTransferItems.objects.all()
    serializer_class = CashTransferItemsSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = CashTransferItemsFilter
    ordering_fields = ("id", "amount")
    ordering = ("id",)
