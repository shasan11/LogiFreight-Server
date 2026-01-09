# operations/filters.py

from django.db import models as dj_models
from django_filters import rest_framework as filters

from .models import (
    Shipment,
    ShipmentDocument,
    ShipmentNote,
    ShipmentTransportInfo,
    ShipmentAdditionalInfo,
    ShipmentWaybillFreightInfo,
    ShipmentPackages,
    ShipmentManifest,
    ShipmentManifestBooking,
    ShipmentManifestHouse,
    PaymentSummary,
    ShipmentCharges,
    ShipmentCostings,
)


class ShipmentFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")
    created = filters.DateFromToRangeFilter()
    updated = filters.DateFromToRangeFilter()
    created_date = filters.DateFromToRangeFilter(field_name="created_date")
    scheduled_start_date = filters.DateFromToRangeFilter(field_name="scheduled_start_date")
    scheduled_end_date = filters.DateFromToRangeFilter(field_name="scheduled_end_date")

    class Meta:
        model = Shipment
        fields = {
            "shipment_main_type": ["exact"],
            "transportation_mode": ["exact"],
            "direction": ["exact"],
            "service_type": ["exact"],
            "origin_port": ["exact", "icontains"],
            "destination_port": ["exact", "icontains"],
            "shipper": ["exact", "icontains"],
            "consignee": ["exact", "icontains"],
            "active": ["exact"],
            "branch": ["exact"],
        }

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(doc_ref_no__icontains=value)
            | dj_models.Q(origin_port__icontains=value)
            | dj_models.Q(destination_port__icontains=value)
            | dj_models.Q(shipper__icontains=value)
            | dj_models.Q(consignee__icontains=value)
        )


class ShipmentDocumentFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")
    created = filters.DateFromToRangeFilter()
    updated = filters.DateFromToRangeFilter()

    class Meta:
        model = ShipmentDocument
        fields = {"shipment": ["exact"], "active": ["exact"], "branch": ["exact"]}

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(dj_models.Q(description__icontains=value))


class ShipmentNoteFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")
    created = filters.DateFromToRangeFilter()
    updated = filters.DateFromToRangeFilter()

    class Meta:
        model = ShipmentNote
        fields = {"shipment": ["exact"], "active": ["exact"], "branch": ["exact"]}

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(dj_models.Q(note__icontains=value) | dj_models.Q(description__icontains=value))


class ShipmentTransportInfoFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")
    created = filters.DateFromToRangeFilter()
    updated = filters.DateFromToRangeFilter()

    class Meta:
        model = ShipmentTransportInfo
        fields = {
            "shipment": ["exact"],
            "leg_type": ["exact"],
            "transport_mode": ["exact"],
            "active": ["exact"],
            "branch": ["exact"],
        }

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(state__icontains=value)
            | dj_models.Q(airline__icontains=value)
            | dj_models.Q(flight_no__icontains=value)
            | dj_models.Q(bill_of_lading__icontains=value)
            | dj_models.Q(tracking_no__icontains=value)
        )


class ShipmentAdditionalInfoFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")
    created = filters.DateFromToRangeFilter()
    updated = filters.DateFromToRangeFilter()

    class Meta:
        model = ShipmentAdditionalInfo
        fields = {
            "shipment": ["exact"],
            "payment": ["exact"],
            "payment_by": ["exact"],
            "active": ["exact"],
            "branch": ["exact"],
        }

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(final_destination__icontains=value)
            | dj_models.Q(place_of_receipt__icontains=value)
            | dj_models.Q(order_no__icontains=value)
            | dj_models.Q(declaration_no__icontains=value)
            | dj_models.Q(salesman__icontains=value)
        )


class ShipmentWaybillFreightInfoFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")

    class Meta:
        model = ShipmentWaybillFreightInfo
        fields = {"shipment": ["exact"], "awb_from_stock": ["exact"], "active": ["exact"], "branch": ["exact"]}

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(air_waybill_no__icontains=value)
            | dj_models.Q(accounting_info__icontains=value)
            | dj_models.Q(exporter_name__icontains=value)
            | dj_models.Q(importer_name__icontains=value)
        )


class ShipmentPackagesFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")
    created = filters.DateFromToRangeFilter()
    updated = filters.DateFromToRangeFilter()

    class Meta:
        model = ShipmentPackages
        fields = {"shipment": ["exact"], "fragile": ["exact"], "active": ["exact"], "branch": ["exact"]}

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(shipment_package__icontains=value)
            | dj_models.Q(good_desc__icontains=value)
            | dj_models.Q(country_of_origin__icontains=value)
            | dj_models.Q(hs_code__icontains=value)
            | dj_models.Q(remarks__icontains=value)
        )


# --- Manifest ---
class ShipmentManifestFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")
    created_at = filters.DateFromToRangeFilter()
    updated_at = filters.DateFromToRangeFilter()

    class Meta:
        model = ShipmentManifest
        fields = {"master_shipment": ["exact"], "manifest_number": ["exact", "icontains"], "manifest_si_number": ["exact", "icontains"]}

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(manifest_number__icontains=value)
            | dj_models.Q(manifest_si_number__icontains=value)
            | dj_models.Q(remarks__icontains=value)
        )


class ShipmentManifestBookingFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")

    class Meta:
        model = ShipmentManifestBooking
        fields = {"shipment_manifest": ["exact"], "shipment": ["exact"], "is_loaded": ["exact"], "is_manifested": ["exact"], "active": ["exact"]}

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(shipment__doc_ref_no__icontains=value)
            | dj_models.Q(shipment_manifest__manifest_number__icontains=value)
        )


class ShipmentManifestHouseFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")

    class Meta:
        model = ShipmentManifestHouse
        fields = {"shipment_manifest": ["exact"], "active": ["exact"], "house_np": ["exact", "icontains"], "waybill_no": ["exact", "icontains"]}

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(house_np__icontains=value)
            | dj_models.Q(waybill_no__icontains=value)
            | dj_models.Q(exporter_name__icontains=value)
            | dj_models.Q(forwader_name__icontains=value)
        )


# --- Payment / Lines ---
class PaymentSummaryFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")
    created = filters.DateFromToRangeFilter()
    updated = filters.DateFromToRangeFilter()

    class Meta:
        model = PaymentSummary
        fields = {"shipment": ["exact"], "currency": ["exact"], "payment_status": ["exact"], "active": ["exact"], "branch": ["exact"]}

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(shipment__doc_ref_no__icontains=value)
            | dj_models.Q(shipment__origin_port__icontains=value)
            | dj_models.Q(shipment__destination_port__icontains=value)
        )


class ShipmentChargesFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")

    class Meta:
        model = ShipmentCharges
        fields = {"payment_summary": ["exact"], "actor": ["exact"], "payable_at": ["exact"]}

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(charge_name__icontains=value)
            | dj_models.Q(reference_no__icontains=value)
            | dj_models.Q(remarks__icontains=value)
        )


class ShipmentCostingsFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")

    class Meta:
        model = ShipmentCostings
        fields = {"payment_summary": ["exact"], "actor": ["exact"], "payable_at": ["exact"]}

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(charge_name__icontains=value)
            | dj_models.Q(reference_no__icontains=value)
            | dj_models.Q(remarks__icontains=value)
        )
