# courier/urls.py
from django.urls import path, include
from rest_framework_bulk.routes import BulkRouter
from .views import (
    VehicleViewSet, RiderViewSet, PickupRequestViewSet, PickupOrderViewSet, PickupPackageViewSet, PickupRunsheetViewSet,
    DeliveryOrderViewSet, DeliveryAttemptViewSet, ProofOfDeliveryViewSet, DeliveryRunsheetViewSet,
    ReturnToVendorViewSet, RtvBranchReturnViewSet, DispatchManifestViewSet, ReceiveManifestViewSet
)

router = BulkRouter()
router.register(r"vehicles", VehicleViewSet, basename="vehicles")
router.register(r"riders", RiderViewSet, basename="riders")
router.register(r"pickup-requests", PickupRequestViewSet, basename="pickup-requests")
router.register(r"pickup-orders", PickupOrderViewSet, basename="pickup-orders")
router.register(r"pickup-packages", PickupPackageViewSet, basename="pickup-packages")
router.register(r"pickup-runsheets", PickupRunsheetViewSet, basename="pickup-runsheets")
router.register(r"delivery-orders", DeliveryOrderViewSet, basename="delivery-orders")
router.register(r"delivery-attempts", DeliveryAttemptViewSet, basename="delivery-attempts")
router.register(r"proof-of-delivery", ProofOfDeliveryViewSet, basename="proof-of-delivery")
router.register(r"delivery-runsheets", DeliveryRunsheetViewSet, basename="delivery-runsheets")
router.register(r"returns-to-vendor", ReturnToVendorViewSet, basename="returns-to-vendor")
router.register(r"rtv-branch-returns", RtvBranchReturnViewSet, basename="rtv-branch-returns")
router.register(r"dispatch-manifests", DispatchManifestViewSet, basename="dispatch-manifests")
router.register(r"receive-manifests", ReceiveManifestViewSet, basename="receive-manifests")

urlpatterns = [path("", include(router.urls))]
