from django.urls import path, include
from rest_framework.routers import DefaultRouter
from actors.views import (
    BookingAgencyViewSet, CarrierViewSet, CustomsAgentViewSet, VendorViewSet,
    CustomerViewSet, DepartmentViewSet, DesignationViewSet, EmployeeViewSet,
    MainActorViewSet,
)

router = DefaultRouter()
router.register(r"booking-agencies", BookingAgencyViewSet, basename="booking-agency")
router.register(r"carriers", CarrierViewSet, basename="carrier")
router.register(r"customs-agents", CustomsAgentViewSet, basename="customs-agent")
router.register(r"vendors", VendorViewSet, basename="vendor")
router.register(r"customers", CustomerViewSet, basename="customer")
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"designations", DesignationViewSet, basename="designation")
router.register(r"employees", EmployeeViewSet, basename="employee")
router.register(r"main-actors", MainActorViewSet, basename="main-actor")

urlpatterns = [
    path("", include(router.urls)),
]
