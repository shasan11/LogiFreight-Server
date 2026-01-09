# api/filters.py
import django_filters as df
from django.db.models import Q

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


class ChartofAccountsFilter(df.FilterSet):
    q = df.CharFilter(method="filter_q")

    class Meta:
        model = ChartofAccounts
        fields = ["type", "active", "branch", "parent_account", "code", "name"]

    def filter_q(self, qs, name, value):
        return qs.filter(Q(code__icontains=value) | Q(name__icontains=value) | Q(description__icontains=value))


class BankAccountsFilter(df.FilterSet):
    q = df.CharFilter(method="filter_q")

    class Meta:
        model = BankAccounts
        fields = ["acc_type", "type", "active", "branch", "currency", "gl_account", "code", "name"]

    def filter_q(self, qs, name, value):
        return qs.filter(
            Q(name__icontains=value)
            | Q(display_name__icontains=value)
            | Q(code__icontains=value)
            | Q(account_number__icontains=value)
        )


class CurrencyFilter(df.FilterSet):
    q = df.CharFilter(method="filter_q")

    class Meta:
        model = Currency
        fields = ["is_default", "active", "name", "symbol"]

    def filter_q(self, qs, name, value):
        return qs.filter(Q(name__icontains=value) | Q(symbol__icontains=value))


class PaymentMethodFilter(df.FilterSet):
    q = df.CharFilter(method="filter_q")

    class Meta:
        model = PaymentMethod
        fields = ["active", "name"]

    def filter_q(self, qs, name, value):
        return qs.filter(Q(name__icontains=value) | Q(description__icontains=value))


class GeneralLedgerFilter(df.FilterSet):
    posting_date_from = df.DateFilter(field_name="posting_date", lookup_expr="gte")
    posting_date_to = df.DateFilter(field_name="posting_date", lookup_expr="lte")

    class Meta:
        model = GeneralLedger
        fields = ["branch", "account", "journal_voucher"]


class JournalVoucherFilter(df.FilterSet):
    q = df.CharFilter(method="filter_q")
    jv_date_from = df.DateFilter(field_name="jv_date", lookup_expr="gte")
    jv_date_to = df.DateFilter(field_name="jv_date", lookup_expr="lte")

    class Meta:
        model = JournalVoucher
        fields = ["approved", "active", "branch", "approved_by", "jv_no"]

    def filter_q(self, qs, name, value):
        return qs.filter(Q(jv_no__icontains=value) | Q(description__icontains=value))


class JournalVoucherItemsFilter(df.FilterSet):
    class Meta:
        model = JournalVoucherItems
        fields = ["journal_voucher", "account", "bank_account"]


class ChequeRegisterFilter(df.FilterSet):
    q = df.CharFilter(method="filter_q")
    issued_received_from = df.DateFilter(field_name="issued_received_date", lookup_expr="gte")
    issued_received_to = df.DateFilter(field_name="issued_received_date", lookup_expr="lte")
    cheque_date_from = df.DateFilter(field_name="cheque_date", lookup_expr="gte")
    cheque_date_to = df.DateFilter(field_name="cheque_date", lookup_expr="lte")

    class Meta:
        model = ChequeRegister
        fields = ["cheque_type", "status", "approved", "active", "bank_account", "offset_account", "branch", "cheque_no"]

    def filter_q(self, qs, name, value):
        return qs.filter(Q(cheque_no__icontains=value) | Q(voided_reason__icontains=value))


class CashTransferFilter(df.FilterSet):
    q = df.CharFilter(method="filter_q")
    ct_date_from = df.DateFilter(field_name="ct_date", lookup_expr="gte")
    ct_date_to = df.DateFilter(field_name="ct_date", lookup_expr="lte")

    class Meta:
        model = CashTransfer
        fields = ["approved", "active", "branch", "from_account", "cash_transfer_no"]

    def filter_q(self, qs, name, value):
        return qs.filter(Q(cash_transfer_no__icontains=value) | Q(description__icontains=value))


class CashTransferItemsFilter(df.FilterSet):
    class Meta:
        model = CashTransferItems
        fields = ["cash_transfer", "to_account"]
