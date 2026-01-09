# courier/serializers.py
from rest_framework import serializers
from rest_framework_bulk.serializers import BulkSerializerMixin
from core.utils.AdaptedBulkListSerializer import AdaptedBulkListSerializer
from .utils import READONLY_FIELDS
from .models import Vehicle, Rider, PickupRequest, PickupOrder, PickupPackage, PickupRunsheet, DeliveryOrder, DeliveryAttempt, ProofOfDelivery, DeliveryRunsheet, ReturnToVendor, RtvBranchReturn, DispatchManifest, ReceiveManifest


class VehicleSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta: model=Vehicle; fields="__all__"; read_only_fields=READONLY_FIELDS; list_serializer_class=AdaptedBulkListSerializer


class RiderSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta: model=Rider; fields="__all__"; read_only_fields=READONLY_FIELDS; list_serializer_class=AdaptedBulkListSerializer


class PickupRequestSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta: model=PickupRequest; fields="__all__"; read_only_fields=READONLY_FIELDS; list_serializer_class=AdaptedBulkListSerializer


class PickupOrderSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta: model=PickupOrder; fields="__all__"; read_only_fields=READONLY_FIELDS; list_serializer_class=AdaptedBulkListSerializer


class PickupPackageSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta: model=PickupPackage; fields="__all__"; read_only_fields=READONLY_FIELDS; list_serializer_class=AdaptedBulkListSerializer


class PickupRunsheetSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta: model=PickupRunsheet; fields="__all__"; read_only_fields=READONLY_FIELDS; list_serializer_class=AdaptedBulkListSerializer


class DeliveryOrderSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta: model=DeliveryOrder; fields="__all__"; read_only_fields=READONLY_FIELDS; list_serializer_class=AdaptedBulkListSerializer


class DeliveryAttemptSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta: model=DeliveryAttempt; fields="__all__"; read_only_fields=READONLY_FIELDS+("attempt_date",); list_serializer_class=AdaptedBulkListSerializer


class ProofOfDeliverySerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta: model=ProofOfDelivery; fields="__all__"; read_only_fields=READONLY_FIELDS+("delivery_time",); list_serializer_class=AdaptedBulkListSerializer


class DeliveryRunsheetSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta: model=DeliveryRunsheet; fields="__all__"; read_only_fields=READONLY_FIELDS; list_serializer_class=AdaptedBulkListSerializer


class ReturnToVendorSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta: model=ReturnToVendor; fields="__all__"; read_only_fields=READONLY_FIELDS; list_serializer_class=AdaptedBulkListSerializer


class RtvBranchReturnSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta: model=RtvBranchReturn; fields="__all__"; read_only_fields=READONLY_FIELDS; list_serializer_class=AdaptedBulkListSerializer


class DispatchManifestSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta: model=DispatchManifest; fields="__all__"; read_only_fields=READONLY_FIELDS; list_serializer_class=AdaptedBulkListSerializer


class ReceiveManifestSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta: model=ReceiveManifest; fields="__all__"; read_only_fields=READONLY_FIELDS; list_serializer_class=AdaptedBulkListSerializer
