from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_bulk import BulkListSerializer, BulkSerializerMixin
from core.utils.AdaptedBulkListSerializer import AdaptedBulkListSerializer
from operations.models import ShipmentPackages
from warehouse.models import (
    Warehouse, Zone, Location, HandlingUnit,
    InboundPlan, Receiving, ReceivingLine, QualityCheck, Putaway,
    Inventory, InventoryMove, CycleCount, CycleCountLine,
    OutboundOrder, Wave, Allocation, Pick, Pack, PackLine, Stage, Load, LoadLine,
)

User = get_user_model()


class BulkStampedModelSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    created = serializers.DateTimeField(read_only=True)
    updated = serializers.DateTimeField(read_only=True)
    user_add = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        list_serializer_class = BulkListSerializer
        update_lookup_field = "id"
        fields = "__all__"
        read_only_fields = ("id", "created", "updated", "user_add")

    def _get_defaults(self):
        req = self.context.get("request")
        user = getattr(req, "user", None)
        defaults = {}
        if user and user.is_authenticated:
            defaults["user_add"] = user
        return defaults

    def create(self, validated_data):
        defaults = self._get_defaults()
        for k, v in defaults.items():
            validated_data.setdefault(k, v)
        return super().create(validated_data)


class WarehouseSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = Warehouse
        list_serializer_class = AdaptedBulkListSerializer


class ZoneSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = Zone
        list_serializer_class = AdaptedBulkListSerializer


class LocationSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = Location
        list_serializer_class = AdaptedBulkListSerializer


class HandlingUnitSerializer(BulkStampedModelSerializer):
    packages = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=ShipmentPackages.objects.all())

    class Meta(BulkStampedModelSerializer.Meta):
        model = HandlingUnit
        list_serializer_class = AdaptedBulkListSerializer


class InboundPlanSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = InboundPlan
        list_serializer_class = AdaptedBulkListSerializer


class ReceivingSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = Receiving
        list_serializer_class = AdaptedBulkListSerializer


class ReceivingLineSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = ReceivingLine
        list_serializer_class = AdaptedBulkListSerializer


class QualityCheckSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = QualityCheck
        list_serializer_class = AdaptedBulkListSerializer


class PutawaySerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = Putaway
        list_serializer_class = AdaptedBulkListSerializer


class InventorySerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = Inventory
        list_serializer_class = AdaptedBulkListSerializer


class InventoryMoveSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = InventoryMove
        list_serializer_class = AdaptedBulkListSerializer


class CycleCountSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = CycleCount
        list_serializer_class = AdaptedBulkListSerializer


class CycleCountLineSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = CycleCountLine
        list_serializer_class = AdaptedBulkListSerializer


class OutboundOrderSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = OutboundOrder
        list_serializer_class = AdaptedBulkListSerializer


class WaveSerializer(BulkStampedModelSerializer):
    orders = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=OutboundOrder.objects.all())

    class Meta(BulkStampedModelSerializer.Meta):
        model = Wave
        list_serializer_class = AdaptedBulkListSerializer


class AllocationSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = Allocation
        list_serializer_class = AdaptedBulkListSerializer


class PickSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = Pick
        list_serializer_class = AdaptedBulkListSerializer


class PackSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = Pack
        list_serializer_class = AdaptedBulkListSerializer


class PackLineSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = PackLine
        list_serializer_class = AdaptedBulkListSerializer


class StageSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = Stage
        list_serializer_class = AdaptedBulkListSerializer


class LoadSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = Load
        list_serializer_class = AdaptedBulkListSerializer


class LoadLineSerializer(BulkStampedModelSerializer):
    class Meta(BulkStampedModelSerializer.Meta):
        model = LoadLine
        list_serializer_class = AdaptedBulkListSerializer
