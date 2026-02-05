from decimal import Decimal

from django.apps import apps
from django.db import transaction
from django.db.models.signals import post_save, pre_save

from accounting.models import Accounts
from purchase.models import VendorBills, VendorPayments


def _norm(s) -> str:
    return (s or "").strip().lower()


def _is_void_or_inactive(instance) -> bool:
    if not getattr(instance, "active", True):
        return True

    status = _norm(getattr(instance, "status", ""))
    bill_status = _norm(getattr(instance, "bill_status", ""))

    if status in {"void", "voided"}:
        return True
    if bill_status in {"void", "voided", "cancelled", "rejected"}:
        return True
    if getattr(instance, "voided_at", None):
        return True
    return False


def _is_approved(instance) -> bool:
    approved = bool(getattr(instance, "approved", False))
    status = _norm(getattr(instance, "status", ""))
    bill_status = _norm(getattr(instance, "bill_status", ""))
    return approved or status == "approved" or bill_status == "approved"


def _should_apply(instance) -> bool:
    return _is_approved(instance) and not _is_void_or_inactive(instance)


def _snapshot_approval_state(instance) -> None:
    if not instance.pk:
        instance._was_applied = False
        return
    try:
        old = type(instance).objects.get(pk=instance.pk)
    except type(instance).DoesNotExist:
        instance._was_applied = False
        return
    instance._was_applied = _should_apply(old)


def _adjust_vendor_account_balance(vendor, delta: Decimal) -> None:
    if not vendor or not getattr(vendor, "main_actor", None):
        return

    delta = Decimal(delta or 0)
    if delta == 0:
        return

    with transaction.atomic():
        account, _ = Accounts.objects.select_for_update().get_or_create(
            actor=vendor.main_actor,
            defaults={
                "name": vendor.main_actor.display_name,
                "branch": vendor.branch,
                "active": getattr(vendor, "active", True),
                "source": Accounts.SourceType.ACTOR,
                "user_add": getattr(vendor, "user_add", None),
            },
        )

        account.balance = (account.balance or Decimal("0")) + delta
        account.name = vendor.main_actor.display_name
        account.branch = vendor.branch
        account.active = getattr(vendor, "active", True)
        account.source = Accounts.SourceType.ACTOR
        account.save(update_fields=["balance", "name", "branch", "active", "source"])


def _apply_if_approved(instance, vendor, delta: Decimal) -> None:
    is_applied = _should_apply(instance)
    was_applied = bool(getattr(instance, "_was_applied", False))

    if is_applied and not was_applied:
        transaction.on_commit(lambda: _adjust_vendor_account_balance(vendor, Decimal(delta)))
    elif was_applied and not is_applied:
        transaction.on_commit(lambda: _adjust_vendor_account_balance(vendor, Decimal(delta) * Decimal("-1")))


def register_purchase_signals() -> None:
    def _pre_save(sender, instance, **kwargs):
        _snapshot_approval_state(instance)

    def _vendor_bill_post_save(sender, instance, created, **kwargs):
        _apply_if_approved(instance, instance.vendor, Decimal(instance.total_amount or 0))

    def _vendor_payment_post_save(sender, instance, created, **kwargs):
        _apply_if_approved(instance, instance.vendor, Decimal(instance.amount or 0) * Decimal("-1"))

    pre_save.connect(_pre_save, sender=VendorBills, dispatch_uid="vendorbills_presave_snapshot")
    pre_save.connect(_pre_save, sender=VendorPayments, dispatch_uid="vendorpayments_presave_snapshot")

    post_save.connect(_vendor_bill_post_save, sender=VendorBills, dispatch_uid="vendorbills_postsave_account_update")
    post_save.connect(_vendor_payment_post_save, sender=VendorPayments, dispatch_uid="vendorpayments_postsave_account_update")

    # Optional model hookup (won't crash if missing)
    PurchaseReturn = apps.get_model("purchase", "PurchaseReturn", require_ready=False) if apps.ready else None
    if PurchaseReturn:
        def _purchase_return_post_save(sender, instance, created, **kwargs):
            # adjust this field if your model uses supplier instead of vendor
            _apply_if_approved(instance, instance.vendor, Decimal(instance.total or 0) * Decimal("-1"))

        pre_save.connect(_pre_save, sender=PurchaseReturn, dispatch_uid="purchasereturn_presave_snapshot")
        post_save.connect(_purchase_return_post_save, sender=PurchaseReturn, dispatch_uid="purchasereturn_postsave_account_update")
