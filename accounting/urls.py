# api/urls.py
from rest_framework_bulk.routes import BulkRouter
from .views import (
    ChartofAccountsViewSet, BankAccountsViewSet, CurrencyViewSet, PaymentMethodViewSet,
    GeneralLedgerViewSet, JournalVoucherViewSet, ChequeRegisterViewSet, CashTransferViewSet,
)

router = BulkRouter()
router.register("coa", ChartofAccountsViewSet)
router.register("bank-accounts", BankAccountsViewSet)
router.register("currencies", CurrencyViewSet)
router.register("payment-methods", PaymentMethodViewSet)
router.register("general-ledger", GeneralLedgerViewSet)
router.register("journal-vouchers", JournalVoucherViewSet)
router.register("cheques", ChequeRegisterViewSet)
router.register("cash-transfers", CashTransferViewSet)


urlpatterns = router.urls
