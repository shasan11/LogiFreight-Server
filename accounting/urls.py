# api/urls.py
from rest_framework.routers import DefaultRouter
from .views import (
    ChartofAccountsViewSet, BankAccountsViewSet, CurrencyViewSet, PaymentMethodViewSet,
    GeneralLedgerViewSet, JournalVoucherViewSet, JournalVoucherItemsViewSet,
    ChequeRegisterViewSet, CashTransferViewSet, CashTransferItemsViewSet
)

router = DefaultRouter()
router.register("coa", ChartofAccountsViewSet)
router.register("bank-accounts", BankAccountsViewSet)
router.register("currencies", CurrencyViewSet)
router.register("payment-methods", PaymentMethodViewSet)
router.register("general-ledger", GeneralLedgerViewSet)
router.register("journal-vouchers", JournalVoucherViewSet)
router.register("journal-voucher-items", JournalVoucherItemsViewSet)
router.register("cheques", ChequeRegisterViewSet)
router.register("cash-transfers", CashTransferViewSet)
router.register("cash-transfer-items", CashTransferItemsViewSet)

urlpatterns = router.urls
