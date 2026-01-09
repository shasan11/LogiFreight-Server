from __future__ import annotations
from django.db import models
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone

from core.utils.getCurrentUser import get_current_user
from core.utils.coreModels import BranchScopedStampedOwnedActive
from master.models import UnitofMeasurement, UnitofMeasurementLength, Ports
from operations.models import Shipment, ShipmentPackages, ShipmentTransportInfo
from actors.models import Vendor


class Warehouse(BranchScopedStampedOwnedActive):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    type = models.CharField(max_length=10, choices=[("self", "Self"), ("agent", "Agent")])
    contact_person = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="warehouse_user_add")

    def __str__(self):
        return self.name or str(self.id)


class Zone(BranchScopedStampedOwnedActive):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="zones")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    temp_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    temp_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_volume = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("0.000000"))
    volume_uom = models.ForeignKey(UnitofMeasurementLength, on_delete=models.PROTECT, null=True, blank=True, related_name="zone_volume_uom")
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="zone_user_add")

    def __str__(self):
        return self.name or str(self.id)


class Location(BranchScopedStampedOwnedActive):
    class LocationType(models.TextChoices):
        RECEIVING = "RECEIVING", "Receiving"
        QC = "QC", "Quality Check"
        STORAGE = "STORAGE", "Storage"
        PICK = "PICK", "Pick Face"
        PACK = "PACK", "Packing"
        STAGE = "STAGE", "Staging"
        DOCK = "DOCK", "Dock"

    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="locations")
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=LocationType.choices, default=LocationType.STORAGE)
    barcode = models.CharField(max_length=60, null=True, blank=True)
    max_volume = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("0.000000"))
    max_gross_weight = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"))
    weight_uom = models.ForeignKey(UnitofMeasurement, on_delete=models.PROTECT, null=True, blank=True, related_name="location_weight_uom")
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="location_user_add")

    def __str__(self):
        return self.code


class HandlingUnit(BranchScopedStampedOwnedActive):
    class HUType(models.TextChoices):
        CARTON = "CARTON", "Carton"
        PALLET = "PALLET", "Pallet"
        CRATE = "CRATE", "Crate"
        BAG = "BAG", "Bag"
        CONTAINER = "CONTAINER", "Container"

    class HUStatus(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        RECEIVED = "RECEIVED", "Received"
        QC_HOLD = "QC_HOLD", "QC Hold"
        STORED = "STORED", "Stored"
        ALLOCATED = "ALLOCATED", "Allocated"
        PICKED = "PICKED", "Picked"
        PACKED = "PACKED", "Packed"
        STAGED = "STAGED", "Staged"
        LOADED = "LOADED", "Loaded"
        DISPATCHED = "DISPATCHED", "Dispatched"

    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="handling_units")
    packages = models.ManyToManyField(ShipmentPackages, blank=True, related_name="handling_units")
    hu_code = models.CharField(max_length=60, db_index=True)
    hu_type = models.CharField(max_length=20, choices=HUType.choices, default=HUType.CARTON)
    status = models.CharField(max_length=20, choices=HUStatus.choices, default=HUStatus.PLANNED)
    gross_weight = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"))
    net_weight = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"))
    volume = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("0.000000"))
    weight_uom = models.ForeignKey(UnitofMeasurement, on_delete=models.PROTECT, null=True, blank=True, related_name="hu_weight_uom")
    volume_uom = models.ForeignKey(UnitofMeasurementLength, on_delete=models.PROTECT, null=True, blank=True, related_name="hu_volume_uom")
    container_no = models.CharField(max_length=50, null=True, blank=True)
    seal_no = models.CharField(max_length=50, null=True, blank=True)
    barcode = models.CharField(max_length=80, null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="hu_user_add")

    def __str__(self):
        return self.hu_code


class InboundPlan(BranchScopedStampedOwnedActive):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        CONFIRMED = "CONFIRMED", "Confirmed"
        ARRIVED = "ARRIVED", "Arrived"
        CLOSED = "CLOSED", "Closed"

    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="inbound_plans")
    transit = models.ForeignKey(ShipmentTransportInfo, on_delete=models.PROTECT, null=True, blank=True, related_name="inbound_plans")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="inbound_plans")
    port_origin = models.ForeignKey(Ports, on_delete=models.PROTECT, null=True, blank=True, related_name="inbound_plans_origin")
    port_destination = models.ForeignKey(Ports, on_delete=models.PROTECT, null=True, blank=True, related_name="inbound_plans_destination")
    handling_agent = models.ForeignKey(Vendor, on_delete=models.PROTECT, null=True, blank=True, related_name="inbound_plans_agent")
    eta = models.DateTimeField(null=True, blank=True)
    dock_location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True, related_name="inbound_plans_dock")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    note = models.TextField(null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="inbound_plan_user_add")

    def __str__(self):
        return f"Inbound {self.id}"


class Receiving(BranchScopedStampedOwnedActive):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        DONE = "DONE", "Done"

    inbound_plan = models.ForeignKey(InboundPlan, on_delete=models.CASCADE, related_name="receivings")
    receiving_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="receivings")
    received_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    note = models.TextField(null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="receiving_user_add")

    def __str__(self):
        return f"Receiving {self.id}"


class ReceivingLine(BranchScopedStampedOwnedActive):
    class Condition(models.TextChoices):
        GOOD = "GOOD", "Good"
        DAMAGED = "DAMAGED", "Damaged"
        MISSING = "MISSING", "Missing"

    receiving = models.ForeignKey(Receiving, on_delete=models.CASCADE, related_name="lines")
    handling_unit = models.ForeignKey(HandlingUnit, on_delete=models.PROTECT, related_name="receiving_lines")
    condition = models.CharField(max_length=10, choices=Condition.choices, default=Condition.GOOD)
    note = models.TextField(null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="receiving_line_user_add")

    def __str__(self):
        return f"{self.receiving_id} - {self.handling_unit_id}"


class QualityCheck(BranchScopedStampedOwnedActive):
    class Result(models.TextChoices):
        PASS = "PASS", "Pass"
        HOLD = "HOLD", "Hold"
        FAIL = "FAIL", "Fail"

    receiving_line = models.OneToOneField(ReceivingLine, on_delete=models.CASCADE, related_name="qc")
    qc_location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True, related_name="qcs")
    result = models.CharField(max_length=10, choices=Result.choices, default=Result.PASS)
    discrepancy = models.TextField(null=True, blank=True)
    checked_at = models.DateTimeField(default=timezone.now)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="qc_user_add")

    def __str__(self):
        return f"QC {self.id}"


class Putaway(BranchScopedStampedOwnedActive):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ASSIGNED = "ASSIGNED", "Assigned"
        DONE = "DONE", "Done"
        CANCELLED = "CANCELLED", "Cancelled"

    handling_unit = models.ForeignKey(HandlingUnit, on_delete=models.PROTECT, related_name="putaways")
    from_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="putaways_from")
    to_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="putaways_to")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="putaways_assigned")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="putaway_user_add")

    def __str__(self):
        return f"Putaway {self.id}"


class Inventory(BranchScopedStampedOwnedActive):
    handling_unit = models.OneToOneField(HandlingUnit, on_delete=models.CASCADE, related_name="inventory")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="inventory")
    on_hand = models.BooleanField(default=True)
    last_moved_at = models.DateTimeField(null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="inventory_user_add")

    def __str__(self):
        return f"{self.handling_unit_id} @ {self.location_id}"


class InventoryMove(BranchScopedStampedOwnedActive):
    class MoveType(models.TextChoices):
        RECEIVE = "RECEIVE", "Receive"
        QC = "QC", "Quality Check"
        PUTAWAY = "PUTAWAY", "Putaway"
        TRANSFER = "TRANSFER", "Transfer"
        ALLOCATE = "ALLOCATE", "Allocate"
        PICK = "PICK", "Pick"
        PACK = "PACK", "Pack"
        STAGE = "STAGE", "Stage"
        LOAD = "LOAD", "Load"
        DISPATCH = "DISPATCH", "Dispatch"
        ADJUST = "ADJUST", "Adjust"

    handling_unit = models.ForeignKey(HandlingUnit, on_delete=models.PROTECT, related_name="moves")
    move_type = models.CharField(max_length=12, choices=MoveType.choices)
    from_location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True, related_name="moves_from")
    to_location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True, related_name="moves_to")
    ref = models.CharField(max_length=80, null=True, blank=True)
    moved_at = models.DateTimeField(default=timezone.now)
    note = models.TextField(null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="inventory_move_user_add")

    def __str__(self):
        return f"{self.move_type} {self.id}"


class CycleCount(BranchScopedStampedOwnedActive):
    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        DONE = "DONE", "Done"

    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="cycle_counts")
    scheduled_date = models.DateField()
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PLANNED)
    note = models.TextField(null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="cycle_count_user_add")

    def __str__(self):
        return f"Count {self.id}"


class CycleCountLine(BranchScopedStampedOwnedActive):
    cycle_count = models.ForeignKey(CycleCount, on_delete=models.CASCADE, related_name="lines")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="cycle_count_lines")
    handling_unit = models.ForeignKey(HandlingUnit, on_delete=models.PROTECT, null=True, blank=True, related_name="cycle_count_lines")
    expected_present = models.BooleanField(default=True)
    found_present = models.BooleanField(default=True)
    note = models.TextField(null=True, blank=True)
    counted_at = models.DateTimeField(null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="cycle_count_line_user_add")

    def __str__(self):
        return f"{self.cycle_count_id} - {self.location_id}"


class OutboundOrder(BranchScopedStampedOwnedActive):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        RELEASED = "RELEASED", "Released"
        PICKING = "PICKING", "Picking"
        PACKING = "PACKING", "Packing"
        STAGED = "STAGED", "Staged"
        DISPATCHED = "DISPATCHED", "Dispatched"
        CLOSED = "CLOSED", "Closed"

    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="outbound_orders")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="outbound_orders")
    requested_ship_date = models.DateField(null=True, blank=True)
    delivery_address = models.TextField(null=True, blank=True)
    priority = models.PositiveSmallIntegerField(default=3)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)
    note = models.TextField(null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="outbound_order_user_add")

    def __str__(self):
        return f"Outbound {self.id}"


class Wave(BranchScopedStampedOwnedActive):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        RUN = "RUN", "Run"
        RELEASED = "RELEASED", "Released"
        DONE = "DONE", "Done"

    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="waves")
    orders = models.ManyToManyField(OutboundOrder, related_name="waves", blank=True)
    planned_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    note = models.TextField(null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="wave_user_add")

    def __str__(self):
        return f"Wave {self.id}"


class Allocation(BranchScopedStampedOwnedActive):
    wave = models.ForeignKey(Wave, on_delete=models.CASCADE, related_name="allocations")
    order = models.ForeignKey(OutboundOrder, on_delete=models.CASCADE, related_name="allocations")
    handling_unit = models.ForeignKey(HandlingUnit, on_delete=models.PROTECT, related_name="allocations")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="allocations")
    allocated_at = models.DateTimeField(default=timezone.now)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="allocation_user_add")

    def __str__(self):
        return f"Alloc {self.id}"


class Pick(BranchScopedStampedOwnedActive):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ASSIGNED = "ASSIGNED", "Assigned"
        PICKED = "PICKED", "Picked"
        CANCELLED = "CANCELLED", "Cancelled"

    allocation = models.OneToOneField(Allocation, on_delete=models.CASCADE, related_name="pick")
    from_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="picks_from")
    to_location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True, related_name="picks_to")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="picks_assigned")
    picked_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="pick_user_add")

    def __str__(self):
        return f"Pick {self.id}"


class Pack(BranchScopedStampedOwnedActive):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        PACKED = "PACKED", "Packed"

    order = models.ForeignKey(OutboundOrder, on_delete=models.CASCADE, related_name="packs")
    pack_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="packs")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    packed_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="pack_user_add")

    def __str__(self):
        return f"Pack {self.id}"


class PackLine(BranchScopedStampedOwnedActive):
    pack = models.ForeignKey(Pack, on_delete=models.CASCADE, related_name="lines")
    handling_unit = models.ForeignKey(HandlingUnit, on_delete=models.PROTECT, related_name="pack_lines")
    label_no = models.CharField(max_length=80, null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="pack_line_user_add")

    def __str__(self):
        return f"{self.pack_id} - {self.handling_unit_id}"


class Stage(BranchScopedStampedOwnedActive):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        STAGED = "STAGED", "Staged"

    order = models.ForeignKey(OutboundOrder, on_delete=models.CASCADE, related_name="stages")
    stage_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="stages")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    staged_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="stage_user_add")

    def __str__(self):
        return f"Stage {self.id}"


class Load(BranchScopedStampedOwnedActive):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        LOADED = "LOADED", "Loaded"
        DISPATCHED = "DISPATCHED", "Dispatched"

    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="loads")
    dock_location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True, related_name="loads")
    vehicle_no = models.CharField(max_length=60, null=True, blank=True)
    driver_name = models.CharField(max_length=120, null=True, blank=True)
    seal_no = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    loaded_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="load_user_add")

    def __str__(self):
        return f"Load {self.id}"


class LoadLine(BranchScopedStampedOwnedActive):
    load = models.ForeignKey(Load, on_delete=models.CASCADE, related_name="lines")
    order = models.ForeignKey(OutboundOrder, on_delete=models.PROTECT, related_name="load_lines")
    handling_unit = models.ForeignKey(HandlingUnit, on_delete=models.PROTECT, related_name="load_lines")
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False, default=get_current_user, related_name="load_line_user_add")

    def __str__(self):
        return f"{self.load_id} - {self.handling_unit_id}"
