import django_filters as df

from crm.models import (
    Lead,
    LeadActivity,
    LeadFollowUp,
    Quotation,
    QuotationPackage,
    QuotationNote,
    QuotationDocument,
    QuotationChargeLine,
    QuotationCostLine,
)


class LeadFilter(df.FilterSet):
    created_from = df.DateTimeFilter(field_name="created", lookup_expr="gte")
    created_to = df.DateTimeFilter(field_name="created", lookup_expr="lte")

    class Meta:
        model = Lead
        fields = [
            "lead_no",
            "status",
            "source",
            "priority",
            "owner",
            "customer",
            "phone",
            "email",
            "company_name",
        ]


class LeadActivityFilter(df.FilterSet):
    activity_from = df.DateTimeFilter(field_name="activity_at", lookup_expr="gte")
    activity_to = df.DateTimeFilter(field_name="activity_at", lookup_expr="lte")

    class Meta:
        model = LeadActivity
        fields = ["lead", "activity_type", "outcome", "created_by"]


class LeadFollowUpFilter(df.FilterSet):
    due_from = df.DateTimeFilter(field_name="due_at", lookup_expr="gte")
    due_to = df.DateTimeFilter(field_name="due_at", lookup_expr="lte")

    class Meta:
        model = LeadFollowUp
        fields = ["lead", "status", "assigned_to"]


class QuotationFilter(df.FilterSet):
    issued_from = df.DateTimeFilter(field_name="issued_date", lookup_expr="gte")
    issued_to = df.DateTimeFilter(field_name="issued_date", lookup_expr="lte")
    expiry_from = df.DateTimeFilter(field_name="expiry_date", lookup_expr="gte")
    expiry_to = df.DateTimeFilter(field_name="expiry_date", lookup_expr="lte")

    class Meta:
        model = Quotation
        fields = [
            "quote_no",
            "status",
            "lead",
            "salesman",
            "transportation_mode",
            "shipping_mode",
            "direction",
            "port_of_departure",
            "port_of_arrival",
            "shipper",
            "consignee",
            "client",
            "charge_currency",
            "invoice_currency",
        ]


class QuotationPackageFilter(df.FilterSet):
    class Meta:
        model = QuotationPackage
        fields = ["quotation", "hs_code", "fragile", "country_of_origin"]


class QuotationNoteFilter(df.FilterSet):
    class Meta:
        model = QuotationNote
        fields = ["quotation"]


class QuotationDocumentFilter(df.FilterSet):
    class Meta:
        model = QuotationDocument
        fields = ["quotation"]


class QuotationChargeLineFilter(df.FilterSet):
    class Meta:
        model = QuotationChargeLine
        fields = ["quotation", "payable_at", "actor", "applied_to", "charge_currency", "invoice_currency"]


class QuotationCostLineFilter(df.FilterSet):
    class Meta:
        model = QuotationCostLine
        fields = ["quotation", "payable_at", "actor", "applied_to", "charge_currency", "invoice_currency"]
