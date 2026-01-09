from __future__ import annotations

import django_filters as df
from django.db.models import Q

from warehouse.models import (
    Warehouse, Zone, Location, HandlingUnit,
    InboundPlan, Receiving, ReceivingLine, QualityCheck, Putaway,
    Inventory, InventoryMove, CycleCount, CycleCountLine,
    OutboundOrder, Wave, Allocation, Pick, Pack, PackLine, Stage, Load, LoadLine,
)


class BaseFilter(df.FilterSet):
    created = df.DateFromToRangeFilter()
    updated = df.DateFromToRangeFilter()
    active = df.BooleanFilter(field_name="active")
    branch = df.CharFilter(field_name="branch_id")


class WarehouseFilter(BaseFilter):
    q = df.CharFilter(method="filter_q")

    class Meta:
        model = Warehouse
        fields = ("type", "branch", "active", "created", "updated")

    def filter_q(self, qs, name, value):
        return qs.filter(Q(name__icontains=value) | Q(code__icontains=value))


class ZoneFilter(BaseFilter):
    warehouse = df.CharFilter(field_name="warehouse_id")
    code = df.CharFilter(field_name="code", lookup_expr="icontains")
    name = df.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Zone
        fields = ("warehouse", "code", "name", "branch", "active", "created", "updated")


class LocationFilter(BaseFilter):
    zone = df.CharFilter(field_name="zone_id")
    type = df.CharFilter(field_name="type")
    code = df.CharFilter(field_name="code", lookup_expr="icontains")

    class Meta:
        model = Location
        fields = ("zone", "type", "code", "branch", "active", "created", "updated")


class HandlingUnitFilter(BaseFilter):
    shipment = df.NumberFilter(field_name="shipment_id")
    status = df.CharFilter(field_name="status")
    hu_code = df.CharFilter(field_name="hu_code", lookup_expr="icontains")
    container_no = df.CharFilter(field_name="container_no", lookup_expr="icontains")

    class Meta:
        model = HandlingUnit
        fields = ("shipment", "status", "hu_code", "container_no", "branch", "active", "created", "updated")


class InboundPlanFilter(BaseFilter):
    shipment = df.NumberFilter(field_name="shipment_id")
    warehouse = df.CharFilter(field_name="warehouse_id")
    status = df.CharFilter(field_name="status")

    class Meta:
        model = InboundPlan
        fields = ("shipment", "warehouse", "status", "branch", "active", "created", "updated")


class ReceivingFilter(BaseFilter):
    inbound_plan = df.CharFilter(field_name="inbound_plan_id")
    status = df.CharFilter(field_name="status")

    class Meta:
        model = Receiving
        fields = ("inbound_plan", "status", "branch", "active", "created", "updated")


class ReceivingLineFilter(BaseFilter):
    receiving = df.CharFilter(field_name="receiving_id")
    handling_unit = df.CharFilter(field_name="handling_unit_id")
    condition = df.CharFilter(field_name="condition")

    class Meta:
        model = ReceivingLine
        fields = ("receiving", "handling_unit", "condition", "branch", "active", "created", "updated")


class QualityCheckFilter(BaseFilter):
    receiving_line = df.CharFilter(field_name="receiving_line_id")
    result = df.CharFilter(field_name="result")

    class Meta:
        model = QualityCheck
        fields = ("receiving_line", "result", "branch", "active", "created", "updated")


class PutawayFilter(BaseFilter):
    handling_unit = df.CharFilter(field_name="handling_unit_id")
    from_location = df.CharFilter(field_name="from_location_id")
    to_location = df.CharFilter(field_name="to_location_id")
    status = df.CharFilter(field_name="status")

    class Meta:
        model = Putaway
        fields = ("handling_unit", "from_location", "to_location", "status", "branch", "active", "created", "updated")


class InventoryFilter(BaseFilter):
    handling_unit = df.CharFilter(field_name="handling_unit_id")
    location = df.CharFilter(field_name="location_id")
    on_hand = df.BooleanFilter(field_name="on_hand")

    class Meta:
        model = Inventory
        fields = ("handling_unit", "location", "on_hand", "branch", "active", "created", "updated")


class InventoryMoveFilter(BaseFilter):
    handling_unit = df.CharFilter(field_name="handling_unit_id")
    move_type = df.CharFilter(field_name="move_type")
    from_location = df.CharFilter(field_name="from_location_id")
    to_location = df.CharFilter(field_name="to_location_id")

    class Meta:
        model = InventoryMove
        fields = ("handling_unit", "move_type", "from_location", "to_location", "branch", "active", "created", "updated")


class CycleCountFilter(BaseFilter):
    warehouse = df.CharFilter(field_name="warehouse_id")
    status = df.CharFilter(field_name="status")
    scheduled_date = df.DateFromToRangeFilter(field_name="scheduled_date")

    class Meta:
        model = CycleCount
        fields = ("warehouse", "status", "scheduled_date", "branch", "active", "created", "updated")


class CycleCountLineFilter(BaseFilter):
    cycle_count = df.CharFilter(field_name="cycle_count_id")
    location = df.CharFilter(field_name="location_id")
    handling_unit = df.CharFilter(field_name="handling_unit_id")

    class Meta:
        model = CycleCountLine
        fields = ("cycle_count", "location", "handling_unit", "branch", "active", "created", "updated")


class OutboundOrderFilter(BaseFilter):
    shipment = df.NumberFilter(field_name="shipment_id")
    warehouse = df.CharFilter(field_name="warehouse_id")
    status = df.CharFilter(field_name="status")
    requested_ship_date = df.DateFromToRangeFilter(field_name="requested_ship_date")

    class Meta:
        model = OutboundOrder
        fields = ("shipment", "warehouse", "status", "requested_ship_date", "branch", "active", "created", "updated")


class WaveFilter(BaseFilter):
    warehouse = df.CharFilter(field_name="warehouse_id")
    status = df.CharFilter(field_name="status")

    class Meta:
        model = Wave
        fields = ("warehouse", "status", "branch", "active", "created", "updated")


class AllocationFilter(BaseFilter):
    wave = df.CharFilter(field_name="wave_id")
    order = df.CharFilter(field_name="order_id")
    handling_unit = df.CharFilter(field_name="handling_unit_id")
    location = df.CharFilter(field_name="location_id")

    class Meta:
        model = Allocation
        fields = ("wave", "order", "handling_unit", "location", "branch", "active", "created", "updated")


class PickFilter(BaseFilter):
    allocation = df.CharFilter(field_name="allocation_id")
    status = df.CharFilter(field_name="status")
    assigned_to = df.CharFilter(field_name="assigned_to_id")

    class Meta:
        model = Pick
        fields = ("allocation", "status", "assigned_to", "branch", "active", "created", "updated")


class PackFilter(BaseFilter):
    order = df.CharFilter(field_name="order_id")
    status = df.CharFilter(field_name="status")
    pack_location = df.CharFilter(field_name="pack_location_id")

    class Meta:
        model = Pack
        fields = ("order", "status", "pack_location", "branch", "active", "created", "updated")


class PackLineFilter(BaseFilter):
    pack = df.CharFilter(field_name="pack_id")
    handling_unit = df.CharFilter(field_name="handling_unit_id")

    class Meta:
        model = PackLine
        fields = ("pack", "handling_unit", "branch", "active", "created", "updated")


class StageFilter(BaseFilter):
    order = df.CharFilter(field_name="order_id")
    status = df.CharFilter(field_name="status")
    stage_location = df.CharFilter(field_name="stage_location_id")

    class Meta:
        model = Stage
        fields = ("order", "status", "stage_location", "branch", "active", "created", "updated")


class LoadFilter(BaseFilter):
    warehouse = df.CharFilter(field_name="warehouse_id")
    status = df.CharFilter(field_name="status")
    dock_location = df.CharFilter(field_name="dock_location_id")

    class Meta:
        model = Load
        fields = ("warehouse", "status", "dock_location", "branch", "active", "created", "updated")


class LoadLineFilter(BaseFilter):
    load = df.CharFilter(field_name="load_id")
    order = df.CharFilter(field_name="order_id")
    handling_unit = df.CharFilter(field_name="handling_unit_id")

    class Meta:
        model = LoadLine
        fields = ("load", "order", "handling_unit", "branch", "active", "created", "updated")
