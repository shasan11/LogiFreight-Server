# courier/views.py
from django.db import transaction
from rest_framework import permissions, filters as drf_filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_bulk.generics import BulkModelViewSet

from .utils import stamp_user_add
from .models import Vehicle, Rider, PickupRequest, PickupOrder, PickupPackage, PickupRunsheet, DeliveryOrder, DeliveryAttempt, ProofOfDelivery, DeliveryRunsheet, ReturnToVendor, RtvBranchReturn, DispatchManifest, ReceiveManifest
from .serializers import VehicleSerializer, RiderSerializer, PickupRequestSerializer, PickupOrderSerializer, PickupPackageSerializer, PickupRunsheetSerializer, DeliveryOrderSerializer, DeliveryAttemptSerializer, ProofOfDeliverySerializer, DeliveryRunsheetSerializer, ReturnToVendorSerializer, RtvBranchReturnSerializer, DispatchManifestSerializer, ReceiveManifestSerializer
from .filters import VehicleFilter, RiderFilter, PickupRequestFilter, PickupOrderFilter, PickupPackageFilter, PickupRunsheetFilter, DeliveryOrderFilter, DeliveryAttemptFilter, ProofOfDeliveryFilter, DeliveryRunsheetFilter, ReturnToVendorFilter, RtvBranchReturnFilter, DispatchManifestFilter, ReceiveManifestFilter
from core.utils.BaseModelViewSet import BaseModelViewSet

class VehicleViewSet(BaseModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    filterset_class = VehicleFilter
    search_fields = ["number_plate","vehicle_type","brand","model"]


class RiderViewSet(BaseModelViewSet):
    queryset = Rider.objects.all()
    serializer_class = RiderSerializer
    filterset_class = RiderFilter
    search_fields = ["full_name","phone","email","license_number"]


class PickupRequestViewSet(BaseModelViewSet):
    queryset = PickupRequest.objects.select_related("Customer").all()
    serializer_class = PickupRequestSerializer
    filterset_class = PickupRequestFilter
    search_fields = ["code","location","time_window","Customer__name"]


class PickupOrderViewSet(BaseModelViewSet):
    queryset = PickupOrder.objects.select_related("pickup_request","vendor","sender_Customer").all()
    serializer_class = PickupOrderSerializer
    filterset_class = PickupOrderFilter
    search_fields = ["code","from_location","destination","receiver_name","receiver_phone","ref_no","sender_Customer__name"]


class PickupPackageViewSet(BaseModelViewSet):
    queryset = PickupPackage.objects.select_related("pickup_order","weight_unit","length_unit").all()
    serializer_class = PickupPackageSerializer
    filterset_class = PickupPackageFilter
    search_fields = ["code","goods_description"]


class PickupRunsheetViewSet(BaseModelViewSet):
    queryset = PickupRunsheet.objects.select_related("vehicle","rider").prefetch_related("pickup_orders").all()
    serializer_class = PickupRunsheetSerializer
    filterset_class = PickupRunsheetFilter
    search_fields = ["code","rider__full_name","vehicle__number_plate"]


class DeliveryOrderViewSet(BaseModelViewSet):
    queryset = DeliveryOrder.objects.select_related("pickup_order","delivered_by").all()
    serializer_class = DeliveryOrderSerializer
    filterset_class = DeliveryOrderFilter
    search_fields = ["code","delivery_address","pickup_order__code","delivered_by__full_name"]


class DeliveryAttemptViewSet(BaseModelViewSet):
    queryset = DeliveryAttempt.objects.select_related("delivery_order").all()
    serializer_class = DeliveryAttemptSerializer
    filterset_class = DeliveryAttemptFilter
    search_fields = ["delivery_order__code","remarks"]


class ProofOfDeliveryViewSet(BaseModelViewSet):
    queryset = ProofOfDelivery.objects.select_related("delivery_order").all()
    serializer_class = ProofOfDeliverySerializer
    filterset_class = ProofOfDeliveryFilter
    search_fields = ["delivery_order__code","recipient_name"]


class DeliveryRunsheetViewSet(BaseModelViewSet):
    queryset = DeliveryRunsheet.objects.select_related("rider","vehicle").prefetch_related("delivery_orders").all()
    serializer_class = DeliveryRunsheetSerializer
    filterset_class = DeliveryRunsheetFilter
    search_fields = ["code","rider__full_name","vehicle__number_plate"]


class ReturnToVendorViewSet(BaseModelViewSet):
    queryset = ReturnToVendor.objects.select_related("vendor","reference_order").all()
    serializer_class = ReturnToVendorSerializer
    filterset_class = ReturnToVendorFilter
    search_fields = ["code","reason","vendor__name"]


class RtvBranchReturnViewSet(BaseModelViewSet):
    queryset = RtvBranchReturn.objects.select_related("pickup_order","from_branch","to_branch").all()
    serializer_class = RtvBranchReturnSerializer
    filterset_class = RtvBranchReturnFilter
    search_fields = ["code","reason"]


class DispatchManifestViewSet(BaseModelViewSet):
    queryset = DispatchManifest.objects.select_related("rider","vehicle").prefetch_related("orders").all()
    serializer_class = DispatchManifestSerializer
    filterset_class = DispatchManifestFilter
    search_fields = ["code","rider__full_name","vehicle__number_plate"]


class ReceiveManifestViewSet(BaseModelViewSet):
    queryset = ReceiveManifest.objects.select_related("from_branch","to_branch").prefetch_related("orders").all()
    serializer_class = ReceiveManifestSerializer
    filterset_class = ReceiveManifestFilter
    search_fields = ["code"]
