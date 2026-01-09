from rest_framework import viewsets, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from actors.models import BookingAgency, Carrier, CustomsAgent, Vendor, Customer, Department, Designation, Employee, MainActor
from actors.serializers import (
    BookingAgencySerializer, CarrierSerializer, CustomsAgentSerializer, VendorSerializer,
    CustomerSerializer, DepartmentSerializer, DesignationSerializer, EmployeeSerializer,
    MainActorSerializer,
)
from actors.filters import (
    BookingAgencyFilter, CarrierFilter, CustomsAgentFilter, VendorFilter, CustomerFilter,
    DepartmentFilter, DesignationFilter, EmployeeFilter, MainActorFilter,
)
from core.utils.BaseModelViewSet import BaseModelViewSet 


class BulkCreateMixin:
    def create(self, request, *args, **kwargs):
        is_many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=is_many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data if not is_many else {})
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class BookingAgencyViewSet(BaseModelViewSet):
    queryset = BookingAgency.objects.all()
    serializer_class = BookingAgencySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BookingAgencyFilter
    search_fields = ["name", "iata_code", "waybill_prefix"]
    ordering_fields = ["name", "created"]


class CarrierViewSet(BaseModelViewSet):
    queryset = Carrier.objects.all()
    serializer_class = CarrierSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CarrierFilter
    search_fields = ["name"]
    ordering_fields = ["name", "created"]


class CustomsAgentViewSet(BaseModelViewSet):
    queryset = CustomsAgent.objects.all()
    serializer_class = CustomsAgentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CustomsAgentFilter
    search_fields = ["name", "mobile", "emirates_no"]
    ordering_fields = ["name", "created"]


class VendorViewSet(BaseModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = VendorFilter
    search_fields = ["name", "trn", "account_no"]
    ordering_fields = ["name", "created"]


class CustomerViewSet(BaseModelViewSet):
    queryset = Customer.objects.all().select_related("currency", "account")
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CustomerFilter
    search_fields = ["mobile_no", "tax_ref_no"]
    ordering_fields = ["created", "mobile_no"]


class DepartmentViewSet(BaseModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DepartmentFilter
    search_fields = ["name"]
    ordering_fields = ["name", "created"]


class DesignationViewSet(BaseModelViewSet):
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DesignationFilter
    search_fields = ["name"]
    ordering_fields = ["name", "created"]


class EmployeeViewSet(BaseModelViewSet):
    queryset = Employee.objects.all().select_related("department", "account").prefetch_related("designations")
    serializer_class = EmployeeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EmployeeFilter
    search_fields = ["first_name", "last_name", "primary_email", "mobile_no"]
    ordering_fields = ["first_name", "last_name", "created"]


class MainActorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MainActor.objects.all()
    serializer_class = MainActorSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MainActorFilter
    search_fields = ["display_name"]
    ordering_fields = ["display_name", "created"]
