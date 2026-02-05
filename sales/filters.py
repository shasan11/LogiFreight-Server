import django_filters as df

from .models import Sales, SalesItem, CustomerPayment, CustomerPaymentItems


class SalesFilter(df.FilterSet):
    invoice_date_from = df.DateFilter(field_name="invoice_date", lookup_expr="gte")
    invoice_date_to = df.DateFilter(field_name="invoice_date", lookup_expr="lte")
    no = df.CharFilter(field_name="no", lookup_expr="icontains")
    reference = df.CharFilter(field_name="reference", lookup_expr="icontains")

    class Meta:
        model = Sales
        fields = ["status", "customer", "currency", "shipment", "branch", "active", "no", "reference"]


class SalesItemFilter(df.FilterSet):
    item_name = df.CharFilter(field_name="item_name", lookup_expr="icontains")

    class Meta:
        model = SalesItem
        fields = ["sales", "vat", "active", "item_name", "branch"]


class CustomerPaymentFilter(df.FilterSet):
    date_from = df.DateFilter(field_name="date", lookup_expr="gte")
    date_to = df.DateFilter(field_name="date", lookup_expr="lte")
    no = df.CharFilter(field_name="no", lookup_expr="icontains")
    payment_reference_number = df.CharFilter(field_name="payment_reference_number", lookup_expr="icontains")

    class Meta:
        model = CustomerPayment
        fields = [
            "status",
            "customer",
            "currency",
            "payment_type",
            "branch",
            "active",
            "approved",
            "no",
            "payment_reference_number",
        ]


class CustomerPaymentItemsFilter(df.FilterSet):
    class Meta:
        model = CustomerPaymentItems
        fields = ["customerpayment", "sales", "active", "branch"]
