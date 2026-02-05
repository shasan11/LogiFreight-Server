from django.shortcuts import render

# Create your views here.
# master/views.py

from django.db import transaction
from rest_framework import permissions, filters as drf_filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_bulk.generics import BulkModelViewSet
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet

from .utils import stamp_user_on_create
from .models import (
    UnitofMeasurement,
    UnitofMeasurementLength,
    Ports,
    Branch,
    MasterData,
    ApplicationSettings,
    ShipmentPrefixes,
)
from .serializers import (
    UnitofMeasurementSerializer,
    UnitofMeasurementLengthSerializer,
    PortsSerializer,
    BranchSerializer,
    MasterDataSerializer,
    ApplicationSettingsSerializer,
    ShipmentPrefixesSerializer,
)
from .filters import (
    UnitofMeasurementFilter,
    UnitofMeasurementLengthFilter,
    PortsFilter,
    BranchFilter,
    MasterDataFilter,
)

from core.utils.BaseModelViewSet import BaseModelViewSet


class UnitofMeasurementViewSet(BulkModelViewSet):
    queryset = UnitofMeasurement.objects.all()
    serializer_class = UnitofMeasurementSerializer
    filterset_class = UnitofMeasurementFilter
    search_fields = ["name", "symbol"]


class UnitofMeasurementLengthViewSet(BulkModelViewSet):
    queryset = UnitofMeasurementLength.objects.all()
    serializer_class = UnitofMeasurementLengthSerializer
    filterset_class = UnitofMeasurementLengthFilter
    search_fields = ["name", "symbol"]


class PortsViewSet(BulkModelViewSet):
    queryset = Ports.objects.select_related("nearest_branch").all()
    serializer_class = PortsSerializer
    filterset_class = PortsFilter
    search_fields = ["name", "symbol", "iso", "iata", "edi", "country", "region", "city"]


class BranchViewSet(BulkModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    filterset_class = BranchFilter
    search_fields = ["branch_id", "name", "city", "state", "country"]


class MasterDataViewSet(BulkModelViewSet):
    queryset = MasterData.objects.all()
    serializer_class = MasterDataSerializer
    filterset_class = MasterDataFilter
    search_fields = ["type_master", "name", "description"]


# ---------- Singletons ----------
class SingletonMixin:
    """
    Exposes:
      GET /.../singleton/
      PUT/PATCH /.../singleton/
    Always returns/updates the single instance (creates one if missing).
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        obj = self.get_queryset().first()
        if obj:
            return obj
        # Create empty instance (model save() blocks duplicates, this is safe)
        serializer = self.get_serializer(data={})
        serializer.is_valid(raise_exception=False)
        return self.get_queryset().model.objects.create()

    @action(detail=False, methods=["get", "put", "patch"], url_path="singleton")
    def singleton(self, request):
        obj = self.get_object()
        if request.method == "GET":
            return Response(self.get_serializer(obj).data)

        serializer = self.get_serializer(obj, data=request.data, partial=(request.method == "PATCH"))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ApplicationSettingsViewSet(SingletonMixin, ModelViewSet):
    queryset = ApplicationSettings.objects.all()
    serializer_class = ApplicationSettingsSerializer
    http_method_names = ["get", "put", "patch", "head", "options"]


class ShipmentPrefixesViewSet(SingletonMixin, ModelViewSet):
    queryset = ShipmentPrefixes.objects.all()
    serializer_class = ShipmentPrefixesSerializer
    http_method_names = ["get", "put", "patch", "head", "options"]
