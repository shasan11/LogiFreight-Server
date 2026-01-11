# purchase/filters.py
import django_filters as df

from .models import (
    VendorBillsGroup, ExpenseCategory, Expenses, ExpensesItems,
    VendorBills, VendorBillItems,
    VendorPayments, VendorPaymentEntries,
    PurchaseReturn, PurchaseReturnItem,
    ExpensePayments, ExpensePaymentEntries,
)


class VendorBillsGroupFilter(df.FilterSet):
    created_from = df.DateFilter(field_name="created", lookup_expr="date__gte")
    created_to = df.DateFilter(field_name="created", lookup_expr="date__lte")

    class Meta:
        model = VendorBillsGroup
        fields = ["no", "status", "branch", "active"]


class ExpenseCategoryFilter(df.FilterSet):
    name = df.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = ExpenseCategory
        fields = ["name", "parent", "active"]


class ExpensesFilter(df.FilterSet):
    date_from = df.DateFilter(field_name="date", lookup_expr="gte")
    date_to = df.DateFilter(field_name="date", lookup_expr="lte")
    due_from = df.DateFilter(field_name="due_date", lookup_expr="gte")
    due_to = df.DateFilter(field_name="due_date", lookup_expr="lte")
    exp_no = df.CharFilter(field_name="exp_no", lookup_expr="icontains")
    invoice_reference = df.CharFilter(field_name="invoice_reference", lookup_expr="icontains")

    class Meta:
        model = Expenses
        fields = ["status", "supplier", "expense_category", "currency", "branch", "active", "exp_no", "invoice_reference"]


class ExpensesItemsFilter(df.FilterSet):
    class Meta:
        model = ExpensesItems
        fields = ["expenses", "vat_choices"]


class VendorBillsFilter(df.FilterSet):
    date_from = df.DateFilter(field_name="date", lookup_expr="gte")
    date_to = df.DateFilter(field_name="date", lookup_expr="lte")
    due_from = df.DateFilter(field_name="due_date", lookup_expr="gte")
    due_to = df.DateFilter(field_name="due_date", lookup_expr="lte")
    no = df.CharFilter(field_name="no", lookup_expr="icontains")
    invoice_reference = df.CharFilter(field_name="invoice_reference", lookup_expr="icontains")

    class Meta:
        model = VendorBills
        fields = ["bill_status", "vendor", "currency", "branch", "active", "no", "vendor_bills_group", "approved", "invoice_reference"]


class VendorBillItemsFilter(df.FilterSet):
    class Meta:
        model = VendorBillItems
        fields = ["vendorbills", "vat_choices", "branch"]


class VendorPaymentsFilter(df.FilterSet):
    date_from = df.DateFilter(field_name="date", lookup_expr="gte")
    date_to = df.DateFilter(field_name="date", lookup_expr="lte")
    no = df.CharFilter(field_name="no", lookup_expr="icontains")
    remarks = df.CharFilter(field_name="remarks", lookup_expr="icontains")

    class Meta:
        model = VendorPayments
        fields = ["status", "vendor", "currency", "branch", "no", "approved", "remarks"]


class VendorPaymentEntriesFilter(df.FilterSet):
    class Meta:
        model = VendorPaymentEntries
        fields = ["vendor_payments", "vendor_bills", "branch"]


class PurchaseReturnFilter(df.FilterSet):
    created_from = df.DateFilter(field_name="created", lookup_expr="date__gte")
    created_to = df.DateFilter(field_name="created", lookup_expr="date__lte")
    no = df.CharFilter(field_name="no", lookup_expr="icontains")
    inv_no = df.CharFilter(field_name="inv_no", lookup_expr="icontains")
    reference_no = df.CharFilter(field_name="reference_no", lookup_expr="icontains")

    class Meta:
        model = PurchaseReturn
        fields = ["vendor", "currency", "branch", "no", "approved", "active", "inv_no", "reference_no"]


class PurchaseReturnItemFilter(df.FilterSet):
    item_name = df.CharFilter(field_name="item_name", lookup_expr="icontains")

    class Meta:
        model = PurchaseReturnItem
        fields = ["purchase_return", "vat", "active", "item_name"]


class ExpensePaymentsFilter(df.FilterSet):
    date_from = df.DateFilter(field_name="date", lookup_expr="gte")
    date_to = df.DateFilter(field_name="date", lookup_expr="lte")
    no = df.CharFilter(field_name="no", lookup_expr="icontains")
    remarks = df.CharFilter(field_name="remarks", lookup_expr="icontains")

    class Meta:
        model = ExpensePayments
        fields = ["status", "currency", "branch", "no", "approved", "remarks"]


class ExpensePaymentEntriesFilter(df.FilterSet):
    class Meta:
        model = ExpensePaymentEntries
        fields = ["expense_payments", "expenses", "branch"]
