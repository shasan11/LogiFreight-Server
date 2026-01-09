import django_filters
from actors.models import BookingAgency, Carrier, CustomsAgent, Vendor, Customer, Department, Designation, Employee, MainActor


class BaseNameFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, qs, name, value):
        return qs.filter(name__icontains=value)


class BookingAgencyFilter(BaseNameFilter):
    class Meta:
        model = BookingAgency
        fields = ["branch", "transportation_mode", "q"]


class CarrierFilter(BaseNameFilter):
    class Meta:
        model = Carrier
        fields = ["branch", "transportation_mode", "q"]


class CustomsAgentFilter(BaseNameFilter):
    class Meta:
        model = CustomsAgent
        fields = ["branch", "mobile", "q"]


class VendorFilter(BaseNameFilter):
    class Meta:
        model = Vendor
        fields = ["branch", "trn", "account_no", "q"]


class CustomerFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, qs, name, value):
        return qs.filter(mobile_no__icontains=value) | qs.filter(tax_ref_no__icontains=value)

    class Meta:
        model = Customer
        fields = ["branch", "customer_type", "q"]


class DepartmentFilter(BaseNameFilter):
    class Meta:
        model = Department
        fields = ["branch", "q"]


class DesignationFilter(BaseNameFilter):
    class Meta:
        model = Designation
        fields = ["branch", "q"]


class EmployeeFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, qs, name, value):
        return qs.filter(primary_email__icontains=value) | qs.filter(mobile_no__icontains=value) | qs.filter(first_name__icontains=value) | qs.filter(last_name__icontains=value)

    class Meta:
        model = Employee
        fields = ["branch", "department", "q"]


class MainActorFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(field_name="display_name", lookup_expr="icontains")
    class Meta:
        model = MainActor
        fields = ["branch", "actor_type", "q"]
