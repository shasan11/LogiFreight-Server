# operations/views.py

from rest_framework.parsers import FormParser, MultiPartParser

from .utils import stamp_user_on_create
from .models import (
    Shipment,
    ShipmentDocument,
    ShipmentNote,
    ShipmentTransportInfo,
    ShipmentPackages,
    ShipmentManifest,
    ShipmentManifestBooking,
    ShipmentManifestHouse,
    PaymentSummary,
    ShipmentCharges,
    ShipmentCostings,
)
from .serializers import (
    ShipmentSerializer,
    ShipmentDocumentSerializer,
    ShipmentNoteSerializer,
    ShipmentTransportInfoSerializer,
    ShipmentPackagesSerializer,
    ShipmentManifestSerializer,
    ShipmentManifestBookingSerializer,
    ShipmentManifestHouseSerializer,
    PaymentSummarySerializer,
    ShipmentChargesSerializer,
    ShipmentCostingsSerializer,
)
from .filters import (
    ShipmentFilter,
    ShipmentDocumentFilter,
    ShipmentNoteFilter,
    ShipmentTransportInfoFilter,
    ShipmentPackagesFilter,
    ShipmentManifestFilter,
    ShipmentManifestBookingFilter,
    ShipmentManifestHouseFilter,
    PaymentSummaryFilter,
    ShipmentChargesFilter,
    ShipmentCostingsFilter,
)

from core.utils.BaseModelViewSet import BaseModelViewSet
class ShipmentViewSet(BaseModelViewSet):
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    filterset_class = ShipmentFilter
    search_fields = ["doc_ref_no", "origin_port", "destination_port", "shipper", "consignee"]


class ShipmentDocumentViewSet(BaseModelViewSet):
    queryset = ShipmentDocument.objects.select_related("shipment").all()
    serializer_class = ShipmentDocumentSerializer
    filterset_class = ShipmentDocumentFilter
    search_fields = ["description"]
    parser_classes = [MultiPartParser, FormParser]  # file upload


class ShipmentNoteViewSet(BaseModelViewSet):
    queryset = ShipmentNote.objects.select_related("shipment").all()
    serializer_class = ShipmentNoteSerializer
    filterset_class = ShipmentNoteFilter
    search_fields = ["note", "description"]


class ShipmentTransportInfoViewSet(BaseModelViewSet):
    queryset = ShipmentTransportInfo.objects.select_related("shipment").all()
    serializer_class = ShipmentTransportInfoSerializer
    filterset_class = ShipmentTransportInfoFilter
    search_fields = ["state", "airline", "flight_no", "bill_of_lading", "tracking_no"]


class ShipmentPackagesViewSet(BaseModelViewSet):
    queryset = ShipmentPackages.objects.select_related("shipment", "package_unit", "mass_unit").all()
    serializer_class = ShipmentPackagesSerializer
    filterset_class = ShipmentPackagesFilter
    search_fields = ["shipment_package", "good_desc", "hs_code", "country_of_origin", "remarks"]


# --- Manifest ---
class ShipmentManifestViewSet(BaseModelViewSet):
    queryset = ShipmentManifest.objects.select_related("master_shipment").all()
    serializer_class = ShipmentManifestSerializer
    filterset_class = ShipmentManifestFilter
    search_fields = ["manifest_number", "manifest_si_number", "remarks"]


class ShipmentManifestBookingViewSet(BaseModelViewSet):
    queryset = ShipmentManifestBooking.objects.select_related("shipment_manifest", "shipment", "house_shipment").prefetch_related("shipment_items_loaded").all()
    serializer_class = ShipmentManifestBookingSerializer
    filterset_class = ShipmentManifestBookingFilter
    search_fields = ["shipment__doc_ref_no", "shipment_manifest__manifest_number"]


class ShipmentManifestHouseViewSet(BaseModelViewSet):
    queryset = ShipmentManifestHouse.objects.select_related("shipment_manifest").prefetch_related("shipment_manifest_booking").all()
    serializer_class = ShipmentManifestHouseSerializer
    filterset_class = ShipmentManifestHouseFilter
    search_fields = ["house_np", "waybill_no", "exporter_name", "forwader_name"]


# --- Payment ---
class PaymentSummaryViewSet(BaseModelViewSet):
    queryset = PaymentSummary.objects.select_related("shipment", "currency").all()
    serializer_class = PaymentSummarySerializer
    filterset_class = PaymentSummaryFilter
    search_fields = ["shipment__doc_ref_no", "shipment__origin_port", "shipment__destination_port"]


class ShipmentChargesViewSet(BaseModelViewSet):
    queryset = ShipmentCharges.objects.select_related("payment_summary", "applied_to", "charge_currency", "invoice_currency", "sales_item").all()
    serializer_class = ShipmentChargesSerializer
    filterset_class = ShipmentChargesFilter
    search_fields = ["charge_name", "reference_no", "remarks"]


class ShipmentCostingsViewSet(BaseModelViewSet):
    queryset = ShipmentCostings.objects.select_related("payment_summary", "applied_to", "charge_currency", "invoice_currency").all()
    serializer_class = ShipmentCostingsSerializer
    filterset_class = ShipmentCostingsFilter
    search_fields = ["charge_name", "reference_no", "remarks"]
