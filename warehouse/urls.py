from __future__ import annotations

from rest_framework_bulk.routes import BulkRouter
from warehouse.views import (
    WarehouseViewSet, ZoneViewSet, LocationViewSet, HandlingUnitViewSet,
    InboundPlanViewSet, ReceivingViewSet, ReceivingLineViewSet, QualityCheckViewSet, PutawayViewSet,
    InventoryViewSet, InventoryMoveViewSet, CycleCountViewSet, CycleCountLineViewSet,
    OutboundOrderViewSet, WaveViewSet, AllocationViewSet, PickViewSet,
    PackViewSet, PackLineViewSet, StageViewSet, LoadViewSet, LoadLineViewSet,
)

router = BulkRouter()
router.register(r"warehouses", WarehouseViewSet, basename="warehouses")
router.register(r"zones", ZoneViewSet, basename="zones")
router.register(r"locations", LocationViewSet, basename="locations")
router.register(r"handling-units", HandlingUnitViewSet, basename="handling-units")
router.register(r"inbound-plans", InboundPlanViewSet, basename="inbound-plans")
router.register(r"receivings", ReceivingViewSet, basename="receivings")
router.register(r"receiving-lines", ReceivingLineViewSet, basename="receiving-lines")
router.register(r"quality-checks", QualityCheckViewSet, basename="quality-checks")
router.register(r"putaways", PutawayViewSet, basename="putaways")
router.register(r"inventories", InventoryViewSet, basename="inventories")
router.register(r"inventory-moves", InventoryMoveViewSet, basename="inventory-moves")
router.register(r"cycle-counts", CycleCountViewSet, basename="cycle-counts")
router.register(r"cycle-count-lines", CycleCountLineViewSet, basename="cycle-count-lines")
router.register(r"outbound-orders", OutboundOrderViewSet, basename="outbound-orders")
router.register(r"waves", WaveViewSet, basename="waves")
router.register(r"allocations", AllocationViewSet, basename="allocations")
router.register(r"picks", PickViewSet, basename="picks")
router.register(r"packs", PackViewSet, basename="packs")
router.register(r"pack-lines", PackLineViewSet, basename="pack-lines")
router.register(r"stages", StageViewSet, basename="stages")
router.register(r"loads", LoadViewSet, basename="loads")
router.register(r"load-lines", LoadLineViewSet, basename="load-lines")

urlpatterns = router.urls
