from decimal import Decimal

from django.apps import apps
from django.db import transaction
from django.db.models.signals import post_save, pre_save

from accounting.models import Accounts


def _norm(s) -> str:
    return (s or "").strip().lower()


def _is_void_or_inactive(instance) -> bool:
    if not getattr(instance, "active", True):
        return True
    status = _norm(getattr(instance, "status", ""))
    if status in {"void", "voided"}:
        return True
    if getattr(instance, "voided_at", None):
        return True
    return False


def _is_approved(instance) -> bool:
    approved = bool(getattr(instance, "approved", False))
    status = _norm(getattr(instance, "status", ""))
    return approved or status == "approved"


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


def _adjust_customer_account_balance(customer, delta: Decimal) -> None:
    if not customer or not getattr(customer, "main_actor", None):
        return

    delta = Decimal(delta or 0)
    if delta == 0:
        return

    with transaction.atomic():
        account, _ = Accounts.objects.select_for_update().get_or_create(
            actor=customer.main_actor,
            defaults={
                "name": customer.main_actor.display_name,
                "branch": getattr(customer, "branch", None),
                "active": getattr(customer, "active", True),
                "source": Accounts.SourceType.ACTOR,
                "user_add": getattr(customer, "user_add", None),
            },
        )

        account.balance = (account.balance or Decimal("0")) + delta
        account.name = customer.main_actor.display_name
        account.branch = getattr(customer, "branch", None)
        account.active = getattr(customer, "active", True)
        account.source = Accounts.SourceType.ACTOR
        account.save(update_fields=["balance", "name", "branch", "active", "source"])


def _apply_if_approved(instance, delta: Decimal) -> None:
    is_applied = _should_apply(instance)
    was_applied = bool(getattr(instance, "_was_applied", False))

    customer = getattr(instance, "customer", None) or getattr(instance, "client", None)

    if is_applied and not was_applied:
        transaction.on_commit(lambda: _adjust_customer_account_balance(customer, Decimal(delta)))
    elif was_applied and not is_applied:
        transaction.on_commit(lambda: _adjust_customer_account_balance(customer, Decimal(delta) * Decimal("-1")))


def register_sales_signals() -> None:
    # Load models safely (no direct import, no circular import pain)
    Sales = apps.get_model("sales", "Sales")
    CustomerPayment = apps.get_model("sales", "CustomerPayment")

    # SalesReturn may not exist in your project. Handle gracefully.
    SalesReturn = None
    try:
        SalesReturn = apps.get_model("sales", "SalesReturn")
    except LookupError:
        SalesReturn = None

    def _pre_save(sender, instance, **kwargs):
        _snapshot_approval_state(instance)

    def _sales_post_save(sender, instance, created, **kwargs):
        _apply_if_approved(instance, Decimal(getattr(instance, "total", 0) or 0))

    def _payment_post_save(sender, instance, created, **kwargs):
        _apply_if_approved(instance, Decimal(getattr(instance, "amount", 0) or 0) * Decimal("-1"))

    pre_save.connect(_pre_save, sender=Sales, dispatch_uid="sales_presave_snapshot")
    pre_save.connect(_pre_save, sender=CustomerPayment, dispatch_uid="custpay_presave_snapshot")

    post_save.connect(_sales_post_save, sender=Sales, dispatch_uid="sales_postsave_account_update")
    post_save.connect(_payment_post_save, sender=CustomerPayment, dispatch_uid="custpay_postsave_account_update")

    if SalesReturn:
        def _sales_return_post_save(sender, instance, created, **kwargs):
            _apply_if_approved(instance, Decimal(getattr(instance, "total", 0) or 0) * Decimal("-1"))

        pre_save.connect(_pre_save, sender=SalesReturn, dispatch_uid="salesreturn_presave_snapshot")
        post_save.connect(_sales_return_post_save, sender=SalesReturn, dispatch_uid="salesreturn_postsave_account_update")
