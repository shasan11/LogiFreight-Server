from django.db import models
from simple_history.models import HistoricalRecords
import uuid
from django.conf import settings
from master.models import Branch

class UUIDPk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class StampedOwnedActive(UUIDPk):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, editable=False)
    active = models.BooleanField(default=True)
    history = HistoricalRecords(inherit=True)
    is_system_generated = models.BooleanField(default=False)

    class Meta:
        abstract = True


class BranchScoped(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT,  related_name="%(class)s_branch", blank=True, null=True)

    class Meta:
        abstract = True

class BranchScopedStampedOwnedActive(StampedOwnedActive, BranchScoped):
    class Meta:
        abstract = True

class TransactionBasedBranchScopedStampedOwnedActive(StampedOwnedActive, BranchScoped):
    approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(blank=True, null=True, verbose_name="Approved At")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, blank=True, null=True, related_name="approved_jvs", verbose_name="Approved By")
    voided_reason=models.TextField(blank=True, null=True)
    voided_at=models.DateTimeField(blank=True, null=True)
    exchange_rate=models.DecimalField(max_digits=18, decimal_places=6, default=1)
    total=models.DecimalField(max_digits=18, decimal_places=6, default=0)
    class Meta:
        abstract = True