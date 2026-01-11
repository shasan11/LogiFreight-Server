# purchase/urls.py  (NO nested routers)
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    VendorBillsGroupViewSet, ExpenseCategoryViewSet,
    ExpensesViewSet, ExpensesItemsViewSet,
    VendorBillsViewSet, VendorBillItemsViewSet,
    VendorPaymentsViewSet, VendorPaymentEntriesViewSet,
    PurchaseReturnViewSet, PurchaseReturnItemViewSet,
    ExpensePaymentsViewSet, ExpensePaymentEntriesViewSet,
)

router = DefaultRouter()
router.register(r"vendor-bills-groups", VendorBillsGroupViewSet, basename="vendor-bills-groups")
router.register(r"expense-categories", ExpenseCategoryViewSet, basename="expense-categories")
router.register(r"expenses", ExpensesViewSet, basename="expenses")
router.register(r"expenses-items", ExpensesItemsViewSet, basename="expenses-items")
router.register(r"vendor-bills", VendorBillsViewSet, basename="vendor-bills")
router.register(r"vendor-bill-items", VendorBillItemsViewSet, basename="vendor-bill-items")
router.register(r"vendor-payments", VendorPaymentsViewSet, basename="vendor-payments")
router.register(r"vendor-payment-entries", VendorPaymentEntriesViewSet, basename="vendor-payment-entries")
router.register(r"purchase-returns", PurchaseReturnViewSet, basename="purchase-returns")
router.register(r"purchase-return-items", PurchaseReturnItemViewSet, basename="purchase-return-items")
router.register(r"expense-payments", ExpensePaymentsViewSet, basename="expense-payments")
router.register(r"expense-payment-entries", ExpensePaymentEntriesViewSet, basename="expense-payment-entries")

urlpatterns = [
    path("api/", include(router.urls)),
]
