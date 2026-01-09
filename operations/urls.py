# operations/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ShipmentViewSet,
    ShipmentDocumentViewSet,
    ShipmentNoteViewSet,
    ShipmentTransportInfoViewSet,
    ShipmentAdditionalInfoViewSet,
    ShipmentWaybillFreightInfoViewSet,
    ShipmentPackagesViewSet,
    ShipmentManifestViewSet,
    ShipmentManifestBookingViewSet,
    ShipmentManifestHouseViewSet,
    PaymentSummaryViewSet,
    ShipmentChargesViewSet,
    ShipmentCostingsViewSet,
)

router = DefaultRouter()

router.register(r"shipments", ShipmentViewSet, basename="shipments")
router.register(r"shipments/documents", ShipmentDocumentViewSet, basename="shipment-documents")
router.register(r"shipments/notes", ShipmentNoteViewSet, basename="shipment-notes")
router.register(r"shipments/transport-info", ShipmentTransportInfoViewSet, basename="shipment-transport-info")
router.register(r"shipments/additional-info", ShipmentAdditionalInfoViewSet, basename="shipment-additional-info")
router.register(r"shipments/waybill-info", ShipmentWaybillFreightInfoViewSet, basename="shipment-waybill-info")
router.register(r"shipments/packages", ShipmentPackagesViewSet, basename="shipment-packages")

router.register(r"manifests", ShipmentManifestViewSet, basename="shipment-manifests")
router.register(r"manifest-bookings", ShipmentManifestBookingViewSet, basename="shipment-manifest-bookings")
router.register(r"manifest-houses", ShipmentManifestHouseViewSet, basename="shipment-manifest-houses")

router.register(r"payment-summaries", PaymentSummaryViewSet, basename="payment-summaries")
router.register(r"shipment-charges", ShipmentChargesViewSet, basename="shipment-charges")
router.register(r"shipment-costings", ShipmentCostingsViewSet, basename="shipment-costings")

urlpatterns = [
    path("", include(router.urls)),
]
