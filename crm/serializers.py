from decimal import Decimal

from rest_framework import serializers
from rest_framework_bulk import BulkListSerializer, BulkSerializerMixin

from crm.models import (
    Lead,
    LeadActivity,
    LeadFollowUp,
    Quotation,
    QuotationDocument,
    QuotationNote,
    QuotationPackage,
    QuotationChargeLine,
    QuotationCostLine,
)


class BulkModelSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        list_serializer_class = BulkListSerializer


class LeadSerializer(BulkModelSerializer):
    class Meta(BulkModelSerializer.Meta):
        model = Lead
        fields = "__all__"
        read_only_fields = ["lead_no", "created", "updated"]


class LeadActivitySerializer(BulkModelSerializer):
    class Meta(BulkModelSerializer.Meta):
        model = LeadActivity
        fields = "__all__"
        read_only_fields = ["created", "updated"]


class LeadFollowUpSerializer(BulkModelSerializer):
    class Meta(BulkModelSerializer.Meta):
        model = LeadFollowUp
        fields = "__all__"
        read_only_fields = ["created", "updated"]


class QuotationSerializer(BulkModelSerializer):
    class Meta(BulkModelSerializer.Meta):
        model = Quotation
        fields = "__all__"
        read_only_fields = [
            "quote_no",
            "subtotal_charge",
            "tax_total_charge",
            "total_charge",
            "subtotal_invoice",
            "tax_total_invoice",
            "total_invoice",
            "created",
            "updated",
        ]


class QuotationDocumentSerializer(BulkModelSerializer):
    class Meta(BulkModelSerializer.Meta):
        model = QuotationDocument
        fields = "__all__"
        read_only_fields = ["created", "updated"]


class QuotationNoteSerializer(BulkModelSerializer):
    class Meta(BulkModelSerializer.Meta):
        model = QuotationNote
        fields = "__all__"
        read_only_fields = ["created", "updated"]


class QuotationPackageSerializer(BulkModelSerializer):
    class Meta(BulkModelSerializer.Meta):
        model = QuotationPackage
        fields = "__all__"
        read_only_fields = ["created", "updated"]


class QuotationChargeLineSerializer(BulkModelSerializer):
    class Meta(BulkModelSerializer.Meta):
        model = QuotationChargeLine
        fields = "__all__"
        read_only_fields = [
            "subtotal_charge",
            "tax_amount_charge",
            "total_with_tax_charge",
            "unit_price_invoice",
            "subtotal_invoice",
            "tax_amount_invoice",
            "total_with_tax_invoice",
            "created",
            "updated",
        ]


class QuotationCostLineSerializer(BulkModelSerializer):
    class Meta(BulkModelSerializer.Meta):
        model = QuotationCostLine
        fields = "__all__"
        read_only_fields = [
            "subtotal_charge",
            "tax_amount_charge",
            "total_with_tax_charge",
            "unit_price_invoice",
            "subtotal_invoice",
            "tax_amount_invoice",
            "total_with_tax_invoice",
            "created",
            "updated",
        ]
