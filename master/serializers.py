# master/serializers.py

from rest_framework import serializers
from rest_framework_bulk.serializers import BulkSerializerMixin
from core.utils.AdaptedBulkListSerializer import AdaptedBulkListSerializer

from .utils import READONLY_FIELDS_CREATED_UPDATED, READONLY_FIELDS_ID_ONLY
from .models import (
    UnitofMeasurement,
    UnitofMeasurementLength,
    Ports,
    Branch,
    MasterData,
    ApplicationSettings,
    ShipmentPrefixes,
)


class UnitofMeasurementSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = UnitofMeasurement
        fields = "__all__"
        read_only_fields = READONLY_FIELDS_CREATED_UPDATED
        list_serializer_class = AdaptedBulkListSerializer


class UnitofMeasurementLengthSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = UnitofMeasurementLength
        fields = "__all__"
        read_only_fields = READONLY_FIELDS_CREATED_UPDATED
        list_serializer_class = AdaptedBulkListSerializer


class PortsSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Ports
        fields = "__all__"
        read_only_fields = READONLY_FIELDS_CREATED_UPDATED
        list_serializer_class = AdaptedBulkListSerializer


class BranchSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"
        read_only_fields = READONLY_FIELDS_CREATED_UPDATED
        list_serializer_class = AdaptedBulkListSerializer


class MasterDataSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = MasterData
        fields = "__all__"
        read_only_fields = ("id", "history")
        list_serializer_class = AdaptedBulkListSerializer


class ApplicationSettingsSerializer(serializers.ModelSerializer):
    """
    Singleton: no bulk needed.
    """
    class Meta:
        model = ApplicationSettings
        fields = "__all__"
        read_only_fields = READONLY_FIELDS_ID_ONLY


class ShipmentPrefixesSerializer(serializers.ModelSerializer):
    """
    Singleton: no bulk needed.
    """
    class Meta:
        model = ShipmentPrefixes
        fields = "__all__"
        read_only_fields = READONLY_FIELDS_ID_ONLY
