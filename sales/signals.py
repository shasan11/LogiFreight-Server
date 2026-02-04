from decimal import Decimal

from django.db import transaction
from django.db.models.signals import post_save, pre_save

from accounting.models import Accounts
from sales.models import CustomerPayment, Sales, SalesReturn


def _snapshot_approval_state(instance) -> None:
    if not instance.pk:
        instance._was_approved = False
        return
    try:
        old = type(instance).objects.get(pk=instance.pk)
    except type(instance).DoesNotExist:
        instance._was_approved = False
        return
    instance._was_approved = old.approved or getattr(old, "status", "") == "approved"


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
                "branch": customer.branch,
                "active": customer.active,
                "source": Accounts.SourceType.ACTOR,
                "user_add": customer.user_add,
            },
        )
        account.balance = (account.balance or Decimal("0")) + delta
        account.name = customer.main_actor.display_name
        account.branch = customer.branch
        account.active = customer.active
        account.source = Accounts.SourceType.ACTOR
        account.save(update_fields=["balance", "name", "branch", "active", "source", "updated"])


def _apply_if_approved(instance, delta: Decimal) -> None:
    is_approved = instance.approved or getattr(instance, "status", "") == "approved"
    was_approved = getattr(instance, "_was_approved", False)
    if is_approved and not was_approved:
        _adjust_customer_account_balance(instance.customer, delta)


def register_sales_signals() -> None:
    def _pre_save(sender, instance, **kwargs):
        _snapshot_approval_state(instance)

    def _sales_post_save(sender, instance: Sales, created, **kwargs):
        _apply_if_approved(instance, Decimal(instance.total or 0))

    def _payment_post_save(sender, instance: CustomerPayment, created, **kwargs):
        _apply_if_approved(instance, Decimal(instance.amount or 0) * Decimal("-1"))

    def _sales_return_post_save(sender, instance: SalesReturn, created, **kwargs):
        _apply_if_approved(instance, Decimal(instance.total or 0) * Decimal("-1"))

    pre_save.connect(_pre_save, sender=Sales, dispatch_uid="sales_presave_snapshot")
    pre_save.connect(_pre_save, sender=CustomerPayment, dispatch_uid="custpay_presave_snapshot")
    pre_save.connect(_pre_save, sender=SalesReturn, dispatch_uid="salesreturn_presave_snapshot")

    post_save.connect(_sales_post_save, sender=Sales, dispatch_uid="sales_postsave_account_update")
    post_save.connect(_payment_post_save, sender=CustomerPayment, dispatch_uid="custpay_postsave_account_update")
    post_save.connect(_sales_return_post_save, sender=SalesReturn, dispatch_uid="salesreturn_postsave_account_update")
