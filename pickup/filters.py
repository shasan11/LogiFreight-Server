# courier/filters.py
from django.db import models as dj_models
from django_filters import rest_framework as filters
from .models import Vehicle, Rider, PickupRequest, PickupOrder, PickupPackage, PickupRunsheet, DeliveryOrder, DeliveryAttempt, ProofOfDelivery, DeliveryRunsheet, ReturnToVendor, RtvBranchReturn, DispatchManifest, ReceiveManifest


class BaseStampedFilter(filters.FilterSet):
    q = filters.CharFilter(method="search")
    created = filters.DateFromToRangeFilter()
    updated = filters.DateFromToRangeFilter()


class VehicleFilter(BaseStampedFilter):
    class Meta: model=Vehicle; fields={"number_plate":["exact","icontains"],"vehicle_type":["exact","icontains"],"active":["exact"],"branch":["exact"]}
    def search(self, qs, name, value): return qs if not value else qs.filter(dj_models.Q(number_plate__icontains=value)|dj_models.Q(vehicle_type__icontains=value)|dj_models.Q(brand__icontains=value)|dj_models.Q(model__icontains=value))


class RiderFilter(BaseStampedFilter):
    class Meta: model=Rider; fields={"full_name":["icontains"],"phone":["icontains"],"gender":["exact"],"active":["exact"],"branch":["exact"]}
    def search(self, qs, name, value): return qs if not value else qs.filter(dj_models.Q(full_name__icontains=value)|dj_models.Q(phone__icontains=value)|dj_models.Q(email__icontains=value)|dj_models.Q(license_number__icontains=value))


class PickupRequestFilter(BaseStampedFilter):
    class Meta: model=PickupRequest; fields={"client":["exact"],"status":["exact"],"requested_date":["exact","gte","lte"],"active":["exact"],"branch":["exact"]}
    def search(self, qs, name, value):
        if not value: return qs
        return qs.filter(dj_models.Q(code__icontains=value)|dj_models.Q(location__icontains=value)|dj_models.Q(time_window__icontains=value)|dj_models.Q(client__name__icontains=value)).distinct()


class PickupOrderFilter(BaseStampedFilter):
    class Meta: model=PickupOrder; fields={"pickup_request":["exact"],"vendor":["exact"],"sender_client":["exact"],"status":["exact"],"active":["exact"],"branch":["exact"]}
    def search(self, qs, name, value):
        if not value: return qs
        return qs.filter(
            dj_models.Q(code__icontains=value)|
            dj_models.Q(from_location__icontains=value)|
            dj_models.Q(destination__icontains=value)|
            dj_models.Q(receiver_name__icontains=value)|
            dj_models.Q(receiver_phone__icontains=value)|
            dj_models.Q(ref_no__icontains=value)|
            dj_models.Q(sender_client__name__icontains=value)
        ).distinct()


class PickupPackageFilter(BaseStampedFilter):
    class Meta: model=PickupPackage; fields={"pickup_order":["exact"],"fragile":["exact"],"active":["exact"],"branch":["exact"]}
    def search(self, qs, name, value): return qs if not value else qs.filter(dj_models.Q(code__icontains=value)|dj_models.Q(goods_description__icontains=value)).distinct()


class PickupRunsheetFilter(BaseStampedFilter):
    class Meta: model=PickupRunsheet; fields={"vehicle":["exact"],"rider":["exact"],"status":["exact"],"active":["exact"],"branch":["exact"]}
    def search(self, qs, name, value):
        if not value: return qs
        return qs.filter(dj_models.Q(code__icontains=value)|dj_models.Q(rider__full_name__icontains=value)|dj_models.Q(vehicle__number_plate__icontains=value)).distinct()


class DeliveryOrderFilter(BaseStampedFilter):
    class Meta: model=DeliveryOrder; fields={"pickup_order":["exact"],"delivery_status":["exact"],"delivery_date":["exact","gte","lte"],"delivered_by":["exact"],"active":["exact"],"branch":["exact"]}
    def search(self, qs, name, value):
        if not value: return qs
        return qs.filter(dj_models.Q(code__icontains=value)|dj_models.Q(delivery_address__icontains=value)|dj_models.Q(pickup_order__code__icontains=value)|dj_models.Q(delivered_by__full_name__icontains=value)).distinct()


class DeliveryAttemptFilter(BaseStampedFilter):
    class Meta: model=DeliveryAttempt; fields={"delivery_order":["exact"],"attempt_number":["exact"],"status":["exact"],"active":["exact"],"branch":["exact"]}
    def search(self, qs, name, value): return qs if not value else qs.filter(dj_models.Q(delivery_order__code__icontains=value)|dj_models.Q(remarks__icontains=value)).distinct()


class ProofOfDeliveryFilter(BaseStampedFilter):
    class Meta: model=ProofOfDelivery; fields={"delivery_order":["exact"],"active":["exact"],"branch":["exact"]}
    def search(self, qs, name, value): return qs if not value else qs.filter(dj_models.Q(delivery_order__code__icontains=value)|dj_models.Q(recipient_name__icontains=value)).distinct()


class DeliveryRunsheetFilter(BaseStampedFilter):
    class Meta: model=DeliveryRunsheet; fields={"rider":["exact"],"vehicle":["exact"],"run_date":["exact","gte","lte"],"status":["exact"],"active":["exact"],"branch":["exact"]}
    def search(self, qs, name, value):
        if not value: return qs
        return qs.filter(dj_models.Q(code__icontains=value)|dj_models.Q(rider__full_name__icontains=value)|dj_models.Q(vehicle__number_plate__icontains=value)).distinct()


class ReturnToVendorFilter(BaseStampedFilter):
    class Meta: model=ReturnToVendor; fields={"vendor":["exact"],"reference_order":["exact"],"status":["exact"],"active":["exact"],"branch":["exact"]}
    def search(self, qs, name, value): return qs if not value else qs.filter(dj_models.Q(code__icontains=value)|dj_models.Q(reason__icontains=value)|dj_models.Q(vendor__name__icontains=value)).distinct()


class RtvBranchReturnFilter(BaseStampedFilter):
    class Meta: model=RtvBranchReturn; fields={"pickup_order":["exact"],"from_branch":["exact"],"to_branch":["exact"],"status":["exact"],"active":["exact"],"branch":["exact"]}
    def search(self, qs, name, value): return qs if not value else qs.filter(dj_models.Q(code__icontains=value)|dj_models.Q(reason__icontains=value)).distinct()


class DispatchManifestFilter(BaseStampedFilter):
    class Meta: model=DispatchManifest; fields={"rider":["exact"],"vehicle":["exact"],"dispatch_date":["exact","gte","lte"],"status":["exact"],"active":["exact"],"branch":["exact"]}
    def search(self, qs, name, value):
        if not value: return qs
        return qs.filter(dj_models.Q(code__icontains=value)|dj_models.Q(rider__full_name__icontains=value)|dj_models.Q(vehicle__number_plate__icontains=value)).distinct()


class ReceiveManifestFilter(BaseStampedFilter):
    class Meta: model=ReceiveManifest; fields={"from_branch":["exact"],"to_branch":["exact"],"receive_date":["exact","gte","lte"],"status":["exact"],"active":["exact"],"branch":["exact"]}
    def search(self, qs, name, value): return qs if not value else qs.filter(dj_models.Q(code__icontains=value)).distinct()
