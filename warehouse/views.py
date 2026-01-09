from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework_bulk import BulkModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from warehouse.utils import log_move
from warehouse.filters import (
    WarehouseFilter, ZoneFilter, LocationFilter, HandlingUnitFilter,
    InboundPlanFilter, ReceivingFilter, ReceivingLineFilter, QualityCheckFilter, PutawayFilter,
    InventoryFilter, InventoryMoveFilter, CycleCountFilter, CycleCountLineFilter,
    OutboundOrderFilter, WaveFilter, AllocationFilter, PickFilter, PackFilter, PackLineFilter, StageFilter, LoadFilter, LoadLineFilter,
)
from warehouse.serializers import (
    WarehouseSerializer, ZoneSerializer, LocationSerializer, HandlingUnitSerializer,
    InboundPlanSerializer, ReceivingSerializer, ReceivingLineSerializer, QualityCheckSerializer, PutawaySerializer,
    InventorySerializer, InventoryMoveSerializer, CycleCountSerializer, CycleCountLineSerializer,
    OutboundOrderSerializer, WaveSerializer, AllocationSerializer, PickSerializer, PackSerializer, PackLineSerializer,
    StageSerializer, LoadSerializer, LoadLineSerializer,
)
from warehouse.models import (
    Warehouse, Zone, Location, HandlingUnit,
    InboundPlan, Receiving, ReceivingLine, QualityCheck, Putaway,
    Inventory, InventoryMove, CycleCount, CycleCountLine,
    OutboundOrder, Wave, Allocation, Pick, Pack, PackLine, Stage, Load, LoadLine,
)

from core.utils.BaseModelViewSet import BaseModelViewSet

def _as_list(x):
    return x if isinstance(x, list) else [x]


 


class WarehouseViewSet(BaseModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    filterset_class = WarehouseFilter
    search_fields = ("name", "code")


class ZoneViewSet(BaseModelViewSet):
    queryset = Zone.objects.select_related("warehouse").all()
    serializer_class = ZoneSerializer
    filterset_class = ZoneFilter
    search_fields = ("name", "code")


class LocationViewSet(BaseModelViewSet):
    queryset = Location.objects.select_related("zone", "zone__warehouse").all()
    serializer_class = LocationSerializer
    filterset_class = LocationFilter
    search_fields = ("code", "name", "barcode")


class HandlingUnitViewSet(BaseModelViewSet):
    queryset = HandlingUnit.objects.select_related("shipment").prefetch_related("packages").all()
    serializer_class = HandlingUnitSerializer
    filterset_class = HandlingUnitFilter
    search_fields = ("hu_code", "barcode", "container_no", "seal_no")


class InboundPlanViewSet(BaseModelViewSet):
    queryset = InboundPlan.objects.select_related("shipment", "warehouse").all()
    serializer_class = InboundPlanSerializer
    filterset_class = InboundPlanFilter
    search_fields = ("note",)


class ReceivingViewSet(BaseModelViewSet):
    queryset = Receiving.objects.select_related("inbound_plan", "receiving_location").all()
    serializer_class = ReceivingSerializer
    filterset_class = ReceivingFilter


class ReceivingLineViewSet(BaseModelViewSet):
    queryset = ReceivingLine.objects.select_related("receiving", "receiving__receiving_location", "handling_unit").all()
    serializer_class = ReceivingLineSerializer
    filterset_class = ReceivingLineFilter

    def perform_create(self, serializer):
        objs = serializer.save()
        user = getattr(self.request, "user", None)
        for obj in _as_list(objs):
            branch = getattr(obj, "branch", None)
            to_location = obj.receiving.receiving_location if obj.receiving_id else None
            log_move(handling_unit=obj.handling_unit, move_type="RECEIVE", from_location=None, to_location=to_location, branch=branch, user=user, ref=str(obj.receiving_id))


class QualityCheckViewSet(BaseModelViewSet):
    queryset = QualityCheck.objects.select_related("receiving_line", "receiving_line__handling_unit").all()
    serializer_class = QualityCheckSerializer
    filterset_class = QualityCheckFilter

    def perform_create(self, serializer):
        objs = serializer.save()
        user = getattr(self.request, "user", None)
        for obj in _as_list(objs):
            branch = getattr(obj, "branch", None)
            hu = obj.receiving_line.handling_unit
            log_move(handling_unit=hu, move_type="QC", from_location=None, to_location=obj.qc_location, branch=branch, user=user, ref=str(obj.receiving_line_id))


class PutawayViewSet(BaseModelViewSet):
    queryset = Putaway.objects.select_related("handling_unit", "from_location", "to_location").all()
    serializer_class = PutawaySerializer
    filterset_class = PutawayFilter

    def perform_update(self, serializer):
        prev = self.get_object()
        objs = serializer.save()
        user = getattr(self.request, "user", None)
        for obj in _as_list(objs):
            if getattr(prev, "status", None) != obj.status and obj.status == "DONE":
                branch = getattr(obj, "branch", None)
                log_move(handling_unit=obj.handling_unit, move_type="PUTAWAY", from_location=obj.from_location, to_location=obj.to_location, branch=branch, user=user, ref=str(obj.id))


class InventoryViewSet(BaseModelViewSet):
    queryset = Inventory.objects.select_related("handling_unit", "location").all()
    serializer_class = InventorySerializer
    filterset_class = InventoryFilter
    search_fields = ("handling_unit__hu_code", "location__code")


class InventoryMoveViewSet(BaseModelViewSet):
    queryset = InventoryMove.objects.select_related("handling_unit", "from_location", "to_location").all()
    serializer_class = InventoryMoveSerializer
    filterset_class = InventoryMoveFilter
    search_fields = ("ref", "note")


class CycleCountViewSet(BaseModelViewSet):
    queryset = CycleCount.objects.select_related("warehouse").all()
    serializer_class = CycleCountSerializer
    filterset_class = CycleCountFilter


class CycleCountLineViewSet(BaseModelViewSet):
    queryset = CycleCountLine.objects.select_related("cycle_count", "location", "handling_unit").all()
    serializer_class = CycleCountLineSerializer
    filterset_class = CycleCountLineFilter


class OutboundOrderViewSet(BaseModelViewSet):
    queryset = OutboundOrder.objects.select_related("shipment", "warehouse").all()
    serializer_class = OutboundOrderSerializer
    filterset_class = OutboundOrderFilter


class WaveViewSet(BaseModelViewSet):
    queryset = Wave.objects.select_related("warehouse").prefetch_related("orders").all()
    serializer_class = WaveSerializer
    filterset_class = WaveFilter


class AllocationViewSet(BaseModelViewSet):
    queryset = Allocation.objects.select_related("wave", "order", "handling_unit", "location").all()
    serializer_class = AllocationSerializer
    filterset_class = AllocationFilter

    def perform_create(self, serializer):
        objs = serializer.save()
        user = getattr(self.request, "user", None)
        for obj in _as_list(objs):
            branch = getattr(obj, "branch", None)
            log_move(handling_unit=obj.handling_unit, move_type="ALLOCATE", from_location=obj.location, to_location=obj.location, branch=branch, user=user, ref=str(obj.order_id))


class PickViewSet(BaseModelViewSet):
    queryset = Pick.objects.select_related("allocation", "allocation__handling_unit", "from_location", "to_location").all()
    serializer_class = PickSerializer
    filterset_class = PickFilter

    def perform_update(self, serializer):
        prev = self.get_object()
        objs = serializer.save()
        user = getattr(self.request, "user", None)
        for obj in _as_list(objs):
            if getattr(prev, "status", None) != obj.status and obj.status == "PICKED":
                branch = getattr(obj, "branch", None)
                hu = obj.allocation.handling_unit
                log_move(handling_unit=hu, move_type="PICK", from_location=obj.from_location, to_location=obj.to_location, branch=branch, user=user, ref=str(obj.allocation_id))


class PackViewSet(BaseModelViewSet):
    queryset = Pack.objects.select_related("order", "pack_location").all()
    serializer_class = PackSerializer
    filterset_class = PackFilter


class PackLineViewSet(BaseModelViewSet):
    queryset = PackLine.objects.select_related("pack", "pack__pack_location", "handling_unit").all()
    serializer_class = PackLineSerializer
    filterset_class = PackLineFilter

    def perform_create(self, serializer):
        objs = serializer.save()
        user = getattr(self.request, "user", None)
        for obj in _as_list(objs):
            branch = getattr(obj, "branch", None)
            to_location = obj.pack.pack_location if obj.pack_id else None
            log_move(handling_unit=obj.handling_unit, move_type="PACK", from_location=None, to_location=to_location, branch=branch, user=user, ref=str(obj.pack_id))


class StageViewSet(BaseModelViewSet):
    queryset = Stage.objects.select_related("order", "stage_location").all()
    serializer_class = StageSerializer
    filterset_class = StageFilter

    def perform_update(self, serializer):
        prev = self.get_object()
        objs = serializer.save()
        user = getattr(self.request, "user", None)
        for obj in _as_list(objs):
            if getattr(prev, "status", None) != obj.status and obj.status == "STAGED":
                branch = getattr(obj, "branch", None)
                for alloc in obj.order.allocations.select_related("handling_unit"):
                    log_move(handling_unit=alloc.handling_unit, move_type="STAGE", from_location=None, to_location=obj.stage_location, branch=branch, user=user, ref=str(obj.order_id))


class LoadViewSet(BaseModelViewSet):
    queryset = Load.objects.select_related("warehouse", "dock_location").all()
    serializer_class = LoadSerializer
    filterset_class = LoadFilter


class LoadLineViewSet(BaseModelViewSet):
    queryset = LoadLine.objects.select_related("load", "load__dock_location", "order", "handling_unit").all()
    serializer_class = LoadLineSerializer
    filterset_class = LoadLineFilter

    def perform_create(self, serializer):
        objs = serializer.save()
        user = getattr(self.request, "user", None)
        for obj in _as_list(objs):
            branch = getattr(obj, "branch", None)
            to_location = obj.load.dock_location if obj.load_id else None
            log_move(handling_unit=obj.handling_unit, move_type="LOAD", from_location=None, to_location=to_location, branch=branch, user=user, ref=str(obj.load_id))
