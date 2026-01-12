# master/filters.py

from django.db import models as dj_models
from django_filters import rest_framework as filters

from .models import (
    UnitofMeasurement,
    UnitofMeasurementLength,
    Ports,
    Branch,
    MasterData,
    ApplicationSettings,
    ShipmentPrefixes,
)


class BaseCreatedUpdatedFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")
    created = filters.DateFromToRangeFilter()
    updated_at = filters.DateFromToRangeFilter()


class UnitofMeasurementFilter(BaseCreatedUpdatedFilter):
    class Meta:
        model = UnitofMeasurement
        fields = {"name": ["exact", "icontains"], "symbol": ["exact", "icontains"], "active": ["exact"]}

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(name__icontains=value) |
            dj_models.Q(symbol__icontains=value)
        )


class UnitofMeasurementLengthFilter(BaseCreatedUpdatedFilter):
    class Meta:
        model = UnitofMeasurementLength
        fields = {"name": ["exact", "icontains"], "symbol": ["exact", "icontains"], "active": ["exact"]}

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(name__icontains=value) |
            dj_models.Q(symbol__icontains=value)
        )


class PortsFilter(BaseCreatedUpdatedFilter):
    class Meta:
        model = Ports
        fields = {
            "name": ["exact", "icontains"],
            "symbol": ["exact", "icontains"],
            "iso": ["exact", "icontains"],
            "iata": ["exact", "icontains"],
            "edi": ["exact", "icontains"],
            "country": ["exact", "icontains"],
            "region": ["exact", "icontains"],
            "city": ["exact", "icontains"],
            "nearest_branch": ["exact"],
            "is_land": ["exact"],
            "is_air": ["exact"],
            "is_sea": ["exact"],
            "active": ["exact"],
        }

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(name__icontains=value) |
            dj_models.Q(symbol__icontains=value) |
            dj_models.Q(iso__icontains=value) |
            dj_models.Q(iata__icontains=value) |
            dj_models.Q(edi__icontains=value) |
            dj_models.Q(country__icontains=value) |
            dj_models.Q(region__icontains=value) |
            dj_models.Q(city__icontains=value)
        )


class BranchFilter(BaseCreatedUpdatedFilter):
    class Meta:
        model = Branch
        fields = {
            "branch_id": ["exact", "icontains"],
            "name": ["exact", "icontains"],
            "city": ["exact", "icontains"],
            "state": ["exact", "icontains"],
            "country": ["exact", "icontains"],
            "status": ["exact"],
            "is_main_branch": ["exact"],
            "active": ["exact"],
        }

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(branch_id__icontains=value) |
            dj_models.Q(name__icontains=value) |
            dj_models.Q(city__icontains=value) |
            dj_models.Q(state__icontains=value) |
            dj_models.Q(country__icontains=value)
        )


class MasterDataFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")

    class Meta:
        model = MasterData
        fields = {"type_master": ["exact"], "name": ["exact", "icontains"], "active": ["exact"]}

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(type_master__icontains=value) |
            dj_models.Q(name__icontains=value) |
            dj_models.Q(description__icontains=value)
        )


class ApplicationSettingsFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")

    class Meta:
        model = ApplicationSettings
        fields = {}

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            dj_models.Q(name__icontains=value) |
            dj_models.Q(country__icontains=value) |
            dj_models.Q(state__icontains=value) |
            dj_models.Q(email__icontains=value) |
            dj_models.Q(phone__icontains=value)
        )


class ShipmentPrefixesFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")

    class Meta:
        model = ShipmentPrefixes
        fields = {}

    def search(self, queryset, name, value):
        if not value:
            return queryset
        # Search across most prefix fields (fast + useful)
        return queryset.filter(
            dj_models.Q(shipment_prefix__icontains=value) |
            dj_models.Q(journal_voucher_prefix__icontains=value) |
            dj_models.Q(invoice_bundle_prefix__icontains=value) |
            dj_models.Q(master_job_prefix__icontains=value) |
            dj_models.Q(booking_prefix__icontains=value)
        )
