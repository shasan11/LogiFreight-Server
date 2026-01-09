# operations/serializers.py

from rest_framework import serializers
from rest_framework_bulk.serializers import BulkSerializerMixin
from core.utils.AdaptedBulkListSerializer import AdaptedBulkListSerializer

from .utils import READONLY_FIELDS
from .models import (
    Shipment,
    ShipmentDocument,
    ShipmentNote,
    ShipmentTransportInfo,
    ShipmentAdditionalInfo,
    ShipmentWaybillFreightInfo,
    ShipmentPackages,
    ShipmentManifest,
    ShipmentManifestBooking,
    ShipmentManifestHouse,
    PaymentSummary,
    ShipmentCharges,
    ShipmentCostings,
)


class ShipmentSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = "__all__"
        read_only_fields = READONLY_FIELDS
        list_serializer_class = AdaptedBulkListSerializer


class ShipmentDocumentSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    document_url = serializers.SerializerMethodField()

    class Meta:
        model = ShipmentDocument
        fields = "__all__"
        read_only_fields = READONLY_FIELDS
        list_serializer_class = AdaptedBulkListSerializer

    def get_document_url(self, obj):
        req = self.context.get("request")
        if not obj.document:
            return None
        try:
            url = obj.document.url
            return req.build_absolute_uri(url) if req else url
        except Exception:
            return None


class ShipmentNoteSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ShipmentNote
        fields = "__all__"
        read_only_fields = READONLY_FIELDS
        list_serializer_class = AdaptedBulkListSerializer


class ShipmentTransportInfoSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ShipmentTransportInfo
        fields = "__all__"
        read_only_fields = READONLY_FIELDS
        list_serializer_class = AdaptedBulkListSerializer


class ShipmentAdditionalInfoSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ShipmentAdditionalInfo
        fields = "__all__"
        read_only_fields = READONLY_FIELDS
        list_serializer_class = AdaptedBulkListSerializer


class ShipmentWaybillFreightInfoSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ShipmentWaybillFreightInfo
        fields = "__all__"
        read_only_fields = READONLY_FIELDS
        list_serializer_class = AdaptedBulkListSerializer


class ShipmentPackagesSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ShipmentPackages
        fields = "__all__"
        read_only_fields = READONLY_FIELDS
        list_serializer_class = AdaptedBulkListSerializer


# --- Manifest ---
class ShipmentManifestSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ShipmentManifest
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")
        list_serializer_class = AdaptedBulkListSerializer


class ShipmentManifestBookingSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ShipmentManifestBooking
        fields = "__all__"
        read_only_fields = ("id",)
        list_serializer_class = AdaptedBulkListSerializer


class ShipmentManifestHouseSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ShipmentManifestHouse
        fields = "__all__"
        read_only_fields = ("id", "created", "updated")
        list_serializer_class = AdaptedBulkListSerializer


# --- Payments / Charges ---
class PaymentSummarySerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = PaymentSummary
        fields = "__all__"
        read_only_fields = READONLY_FIELDS
        list_serializer_class = AdaptedBulkListSerializer


class ShipmentChargesSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ShipmentCharges
        fields = "__all__"
        read_only_fields = ("id", "created", "updated")
        list_serializer_class = AdaptedBulkListSerializer


class ShipmentCostingsSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ShipmentCostings
        fields = "__all__"
        read_only_fields = ("id", "created", "updated")
        list_serializer_class = AdaptedBulkListSerializer
