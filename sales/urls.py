from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SalesViewSet, SalesItemViewSet, CustomerPaymentViewSet, CustomerPaymentItemsViewSet

router = DefaultRouter()
router.register(r"sales", SalesViewSet, basename="sales")
router.register(r"sales-items", SalesItemViewSet, basename="sales-items")
router.register(r"customer-payments", CustomerPaymentViewSet, basename="customer-payments")
router.register(r"customer-payment-items", CustomerPaymentItemsViewSet, basename="customer-payment-items")

urlpatterns = [
    path("", include(router.urls)),
]
