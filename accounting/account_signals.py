from django.db.models.signals import post_save

from accounting.models import Accounts, BankAccounts, ChartofAccounts
from actors.models import MainActor


def _upsert_account_for_chart(instance, *, created: bool) -> None:
    defaults = {
        "name": instance.name,
        "branch": instance.branch,
        "active": instance.active,
        "source": Accounts.SourceType.CHART_OF_ACCOUNTS,
        "user_add": instance.user_add,
    }
    if created:
        Accounts.objects.create(chart_account=instance, **defaults)
        return
    Accounts.objects.update_or_create(chart_account=instance, defaults=defaults)


def _upsert_account_for_bank(instance, *, created: bool) -> None:
    defaults = {
        "name": instance.name,
        "branch": instance.branch,
        "active": instance.active,
        "source": Accounts.SourceType.BANK_ACCOUNT,
        "user_add": instance.user_add,
    }
    if created:
        Accounts.objects.create(bank_account=instance, **defaults)
        return
    Accounts.objects.update_or_create(bank_account=instance, defaults=defaults)


def _upsert_account_for_actor(instance, *, created: bool) -> None:
    defaults = {
        "name": instance.display_name,
        "branch": instance.branch,
        "active": instance.active,
        "source": Accounts.SourceType.ACTOR,
        "user_add": instance.user_add,
    }
    if created:
        Accounts.objects.create(actor=instance, **defaults)
        return
    Accounts.objects.update_or_create(actor=instance, defaults=defaults)


def register_account_signals() -> None:
    def _chart_post_save(sender, instance, created, **kwargs):
        _upsert_account_for_chart(instance, created=created)

    def _bank_post_save(sender, instance, created, **kwargs):
        _upsert_account_for_bank(instance, created=created)

    def _actor_post_save(sender, instance, created, **kwargs):
        _upsert_account_for_actor(instance, created=created)

    post_save.connect(_chart_post_save, sender=ChartofAccounts, dispatch_uid="accounts_postsave_coa")
    post_save.connect(_bank_post_save, sender=BankAccounts, dispatch_uid="accounts_postsave_bank")
    post_save.connect(_actor_post_save, sender=MainActor, dispatch_uid="accounts_postsave_actor")
