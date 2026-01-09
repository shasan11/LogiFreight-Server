# master/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UnitofMeasurementViewSet,
    UnitofMeasurementLengthViewSet,
    PortsViewSet,
    BranchViewSet,
    MasterDataViewSet,
    ApplicationSettingsViewSet,
    ShipmentPrefixesViewSet,
)

router = DefaultRouter()
router.register(r"units", UnitofMeasurementViewSet, basename="units")
router.register(r"units-length", UnitofMeasurementLengthViewSet, basename="units-length")
router.register(r"ports", PortsViewSet, basename="ports")
router.register(r"branches", BranchViewSet, basename="branches")
router.register(r"master-data", MasterDataViewSet, basename="master-data")

# Singletons still registered as viewsets, but you’ll use /singleton/
router.register(r"app-settings", ApplicationSettingsViewSet, basename="app-settings")
router.register(r"shipment-prefixes", ShipmentPrefixesViewSet, basename="shipment-prefixes")

urlpatterns = [
    path("", include(router.urls)),
]
