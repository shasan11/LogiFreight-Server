from django.db import models

# Create your models here.
from decimal import Decimal
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q, Sum
from django.utils import timezone
from simple_history.models import HistoricalRecords
from core.utils.coreModels import TransactionBasedBranchScopedStampedOwnedActive,BranchScoped
from actors.models import *
def get_current_user(): return None
def get_current_user_branch(): return None

def _enforce_void_reason_and_no_reactivation(instance, *, has_void_field=True):
    if not hasattr(instance, "active"): return
    if instance.pk:
        try:
            old = instance.__class__.objects.get(pk=instance.pk)
            if old.active is False and instance.active is True: raise ValidationError({"active": "Reactivation is not allowed once a record has been deactivated."})
        except instance.__class__.DoesNotExist:
            pass
    if instance.active is False and has_void_field and hasattr(instance, "voided_reason"):
        reason = (instance.voided_reason or "").strip()
        if not reason: raise ValidationError({"voided_reason": "Voided reason is required when deactivating this record."})

class ChartofAccounts(BranchScoped):
    TYPE_CHOICES = [("asset", "Asset"), ("liability", "Liability"), ("equity", "Equity"), ("income", "Income"), ("expense", "Expense")]
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Account Name")
    code = models.CharField(max_length=20, unique=True, verbose_name="Account Code")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Account Type")
    parent_account = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True, related_name="sub_accounts", verbose_name="Parent Account")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    user_add = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, default=get_current_user)
    active = models.BooleanField(default=True, verbose_name="Is Active")
    history = HistoricalRecords()
    branch = models.ForeignKey("Branch", on_delete=models.PROTECT, verbose_name="Branch", default=get_current_user_branch, related_name="chart_of_acc_branch", blank=True, null=True)

    def __str__(self): return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = "Chart of Account"
        verbose_name_plural = "Chart of Accounts"
        ordering = ["code"]
        indexes = [models.Index(fields=["code"]), models.Index(fields=["type"])]

class BankAccounts(BranchScoped):
    ACC_TYPE_CHOICES = [("Cash", "Cash"), ("Bank", "Bank")]
    TYPE_CHOICES = [("savings", "Savings"), ("current", "Current")]
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    acc_type = models.CharField(max_length=100, choices=ACC_TYPE_CHOICES, default="Bank", verbose_name="Bank/Cash")
    name = models.CharField(max_length=255, verbose_name="Account Name")
    display_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Bank Name")
    code = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="Account Code")
    currency = models.ForeignKey("Currency", on_delete=models.CASCADE, blank=True, null=True, related_name="bank_accounts", verbose_name="Currency")
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Opening Balance")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, blank=True, null=True, verbose_name="Account Type")
    account_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Account Number")
    gl_account = models.OneToOneField(ChartofAccounts, on_delete=models.PROTECT, related_name="bank_details", limit_choices_to={"type": "asset"}, verbose_name="GL Account", null=True, blank=True, help_text="The GL account (in COA) representing this bank/cash account.")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    

    def __str__(self): return self.name

    def clean(self):
        if self.gl_account and self.gl_account.type != "asset": raise ValidationError("Linked GL account must be an Asset type for Bank/Cash.")

    class Meta:
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"
        ordering = ["name"]
        indexes = [models.Index(fields=["code"])]
        constraints = [models.UniqueConstraint(fields=["branch", "code"], name="uniq_bank_code_per_branch_nonnull_nonempty", condition=Q(code__isnull=False) & ~Q(code=""))]

class Currency(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Currency Name")
    symbol = models.CharField(max_length=10, verbose_name="Symbol")
    conversion_to_default = models.DecimalField(verbose_name="Conversion to Default", default=1, max_digits=1000, decimal_places=2, validators=[MinValueValidator(0)])
    is_default = models.BooleanField(default=False, verbose_name="Is Default")
    

    def __str__(self): return self.name

    def clean(self):
        if self.is_default and str(self.conversion_to_default) != "1": raise ValidationError({"conversion_to_default": "Default currency must have a conversion factor of 1."})

    class Meta:
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"

class PaymentMethod(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=50, unique=True, verbose_name="Payment Method Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    commission = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)], verbose_name="Commission (%)")
     

    def __str__(self): return self.name

class GeneralLedger(BranchScoped):
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    posting_date = models.DateField(default=timezone.now)
    account = models.ForeignKey(ChartofAccounts, on_delete=models.PROTECT, related_name="ledger_entries")
    journal_voucher = models.ForeignKey("JournalVoucher", on_delete=models.PROTECT, related_name="ledger_entries", null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
     
    class Meta:
        verbose_name = "General Ledger Entry"
        verbose_name_plural = "General Ledger Entries"
        indexes = [models.Index(fields=["posting_date"]), models.Index(fields=["account"]), models.Index(fields=["journal_voucher"])]

class JournalVoucher(TransactionBasedBranchScopedStampedOwnedActive):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)
    jv_no = models.CharField(max_length=50, verbose_name="Journal Voucher Number", default="#DRAFT")
    jv_date = models.DateField(default=timezone.now, verbose_name="Journal Voucher Date")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
     

    def __str__(self): return f"JV {self.jv_no} ({self.jv_date})"

    @property
    def total_debit(self) -> Decimal:
        agg = self.items.aggregate(x=Sum("debit"))
        return agg["x"] or Decimal("0")

    @property
    def total_credit(self) -> Decimal:
        agg = self.items.aggregate(x=Sum("credit"))
        return agg["x"] or Decimal("0")

    @property
    def is_balanced(self) -> bool:
        return self.total_debit == self.total_credit and self.total_debit > 0

    def _generate_jv_number(self) -> str:
        today = timezone.localdate()
        suffix = uuid.uuid4().hex[:6].upper()
        return f"JV-{today.strftime('%Y%m%d')}-{suffix}"

    def _validate_before_approval(self):
        if self.items.count() == 0: raise ValidationError("Cannot approve a JV with no items.")
        if not self.is_balanced: raise ValidationError({"approved": f"Debits ({self.total_debit}) must equal Credits ({self.total_credit}) and be > 0 before approval."})
        if self.items.filter(account__active=False).exists(): raise ValidationError({"items": "One or more JV items reference an inactive GL account."})

    def _post_to_gl(self):
        if self.ledger_entries.exists(): return
        gl_rows = [GeneralLedger(posting_date=self.jv_date, account=item.account, journal_voucher=self, description=item.description or self.description, debit=item.debit or Decimal("0"), credit=item.credit or Decimal("0"), branch=self.branch) for item in self.items.select_related("account")]
        GeneralLedger.objects.bulk_create(gl_rows)

    def clean(self):
        _enforce_void_reason_and_no_reactivation(self, has_void_field=True)
        if self.approved: self._validate_before_approval()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        with transaction.atomic():
            old_approved = False
            if not is_new:
                try:
                    old = JournalVoucher.objects.select_for_update().get(pk=self.pk)
                    old_approved = old.approved
                except JournalVoucher.DoesNotExist:
                    pass
            if (self.jv_no or "").startswith("#") and self.approved: self.jv_no = self._generate_jv_number()
            super().save(*args, **kwargs)
            if self.approved and not old_approved:
                self._validate_before_approval()
                self._post_to_gl()
                self.approved_at = timezone.now()
                if not self.approved_by: self.approved_by = self.user_add
                super().save(update_fields=["approved_at", "approved_by"])

    class Meta:
        verbose_name = "Journal Voucher"
        verbose_name_plural = "Journal Vouchers"
        ordering = ["-jv_date", "-id"]
        indexes = [models.Index(fields=["jv_no"])]
        constraints = [models.UniqueConstraint(fields=["jv_no"], name="uniq_jv_no_when_final", condition=~Q(jv_no__startswith="#"))]

class JournalVoucherItems(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)
    journal_voucher = models.ForeignKey(JournalVoucher, on_delete=models.CASCADE, related_name="items", verbose_name="Journal Voucher")
    account = models.ForeignKey(ChartofAccounts, on_delete=models.PROTECT, related_name="journal_voucher_items", verbose_name="Account")
    debit = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Debit Amount", default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Credit Amount", default=0)
    bank_account = models.ForeignKey("BankAccounts", on_delete=models.PROTECT, null=True, blank=True, related_name="journal_items", verbose_name="Bank/Cash Account (optional)", help_text="If set, its GL must match the selected Account.")
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    def __str__(self):
        side = "Dr" if (self.debit or 0) > 0 else "Cr"
        amount = self.debit if (self.debit or 0) > 0 else self.credit
        return f"JV Item - {self.account.name} {side} {amount}"

    def clean(self):
        d, c = self.debit or 0, self.credit or 0
        if d > 0 and c > 0: raise ValidationError("Both debit and credit cannot be non-zero at the same time.")
        if d == 0 and c == 0: raise ValidationError("Either debit or credit must be greater than zero.")
        if self.journal_voucher and self.journal_voucher.approved: raise ValidationError("Cannot modify items of an approved Journal Voucher.")
        if self.bank_account:
            if not self.bank_account.gl_account: raise ValidationError("Selected bank account is not linked to any GL account.")
            if self.bank_account.gl_account_id != self.account_id: raise ValidationError("Bank account’s GL does not match the selected Account.")

    class Meta:
        verbose_name = "Journal Voucher Item"
        verbose_name_plural = "Journal Voucher Items"
        ordering = ["id"]
        constraints = [models.CheckConstraint(check=~(models.Q(debit__gt=0) & models.Q(credit__gt=0)), name="jvi_not_both_debit_credit_positive"), models.CheckConstraint(check=(models.Q(debit__gt=0) | models.Q(credit__gt=0)), name="jvi_at_least_one_side_positive")]

class ChequeRegister(TransactionBasedBranchScopedStampedOwnedActive):
    CHEQUE_CHOICES = [("recieved", "Cheque Received"), ("issued", "Cheque Issued")]
    STATUS_CHOICES = [("cleared", "Cleared"), ("pending", "Pending"), ("partial", "Partial"), ("bounced", "Bounced")]
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)
    cheque_no = models.CharField(max_length=50, verbose_name="Cheque Number")
    cheque_type = models.CharField(max_length=10, choices=CHEQUE_CHOICES, verbose_name="Cheque Type")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)], verbose_name="Cheque Amount")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="cheques", verbose_name="Customer", blank=True, null=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="cheques", verbose_name="Vendor", blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="cheques", verbose_name="Supplier", blank=True, null=True)
    bank_account = models.ForeignKey(BankAccounts, on_delete=models.CASCADE, related_name="cheques", verbose_name="Bank Account")
    offset_account = models.ForeignKey(ChartofAccounts, on_delete=models.PROTECT, related_name="cheque_offset_for", verbose_name="Offset/Counterpart Account", help_text="Account to offset the bank/cash when cheque clears (e.g., AR, AP, Expense).", blank=True, null=True)
    issued_received_date = models.DateField(verbose_name="Issued/Received Date")
    cheque_date = models.DateField(verbose_name="Cheque Date")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending", verbose_name="Cheque Status")
    journal_voucher = models.OneToOneField("JournalVoucher", on_delete=models.PROTECT, null=True, blank=True, related_name="from_cheque")
     

    def __str__(self): return f"Cheque {self.cheque_no}"

    def clean(self):
        _enforce_void_reason_and_no_reactivation(self, has_void_field=True)
        if self.approved and not self.offset_account: raise ValidationError({"offset_account": "Offset account is required when approving a cheque."})
        if self.bank_account and not self.bank_account.gl_account: raise ValidationError({"bank_account": "Selected bank account is not linked to any GL account."})

    def _ensure_posted_on_clear(self):
        if self.status != "cleared" or not self.approved or self.journal_voucher_id: return
        if not self.offset_account: raise ValidationError("Offset account required to post cheque.")
        if not self.bank_account.gl_account: raise ValidationError("Bank account must be linked to a GL account to post cheque.")
        with transaction.atomic():
            jv = JournalVoucher.objects.create(jv_no="#DRAFT", jv_date=timezone.localdate(), description=f"Cheque {self.cheque_no} {self.get_cheque_type_display()} cleared", user_add=self.user_add, branch=self.branch)
            bank_gl, amt = self.bank_account.gl_account, self.amount
            if self.cheque_type == "recieved":
                JournalVoucherItems.objects.create(journal_voucher=jv, account=bank_gl, bank_account=self.bank_account, debit=amt, credit=0, description=f"Cheque {self.cheque_no} received")
                JournalVoucherItems.objects.create(journal_voucher=jv, account=self.offset_account, debit=0, credit=amt, description=f"Cheque {self.cheque_no} received")
            else:
                JournalVoucherItems.objects.create(journal_voucher=jv, account=self.offset_account, debit=amt, credit=0, description=f"Cheque {self.cheque_no} issued")
                JournalVoucherItems.objects.create(journal_voucher=jv, account=bank_gl, bank_account=self.bank_account, debit=0, credit=amt, description=f"Cheque {self.cheque_no} issued")
            jv.approved, jv.approved_by = True, self.user_add
            jv.save()
            self.journal_voucher = jv
            super().save(update_fields=["journal_voucher"])

    def save(self, *args, **kwargs):
        with transaction.atomic():
            is_new, old_status = self.pk is None, None
            if not is_new:
                try:
                    old = ChequeRegister.objects.select_for_update().get(pk=self.pk)
                    old_status = old.status
                except ChequeRegister.DoesNotExist:
                    pass
            super().save(*args, **kwargs)
            if self.status == "cleared" and old_status != "cleared": self._ensure_posted_on_clear()

    class Meta:
        verbose_name = "Cheque Register"
        verbose_name_plural = "Cheque Register"
        constraints = [models.UniqueConstraint(fields=["bank_account", "cheque_no"], name="uniq_cheque_no_per_bank")]

class CashTransfer(TransactionBasedBranchScopedStampedOwnedActive):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)
    cash_transfer_no = models.CharField(max_length=50, verbose_name="Cash Transfer Number", default="#DRAFT")
    from_account = models.ForeignKey(BankAccounts, on_delete=models.CASCADE, related_name="cash_transfers_out", verbose_name="From Account")
    ct_date = models.DateField(default=timezone.now, verbose_name="Transfer Date")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    journal_voucher = models.OneToOneField("JournalVoucher", on_delete=models.PROTECT, null=True, blank=True, related_name="from_cash_transfer")

    def __str__(self): return f"CT {self.cash_transfer_no} ({self.ct_date})"

    def clean(self):
        _enforce_void_reason_and_no_reactivation(self, has_void_field=True)
        if not self.from_account.gl_account: raise ValidationError({"from_account": "From Account must be linked to a GL account."})

    def _generate_ct_number(self) -> str:
        today = timezone.localdate()
        suffix = uuid.uuid4().hex[:6].upper()
        return f"CT-{today.strftime('%Y%m%d')}-{suffix}"

    def _ensure_jv(self):
        if self.journal_voucher_id: return
        if not self.items.exists(): raise ValidationError("Cannot approve a Cash Transfer with no items.")
        with transaction.atomic():
            jv = JournalVoucher.objects.create(jv_no="#DRAFT", jv_date=self.ct_date, description=f"Cash Transfer {self.cash_transfer_no}", user_add=self.user_add, branch=self.branch)
            total_amount = Decimal("0")
            for it in self.items.select_related("to_account"):
                JournalVoucherItems.objects.create(journal_voucher=jv, account=it.to_account.gl_account, bank_account=it.to_account, debit=it.amount, credit=0, description=it.description or self.description)
                total_amount += it.amount
            JournalVoucherItems.objects.create(journal_voucher=jv, account=self.from_account.gl_account, bank_account=self.from_account, debit=0, credit=total_amount, description=self.description or "Transfer out")
            jv.approved, jv.approved_by = True, self.user_add
            jv.save()
            self.journal_voucher = jv
            super().save(update_fields=["journal_voucher"])

    def save(self, *args, **kwargs):
        with transaction.atomic():
            is_new, old_approved = self.pk is None, False
            if not is_new:
                try:
                    old = CashTransfer.objects.select_for_update().get(pk=self.pk)
                    old_approved = old.approved
                except CashTransfer.DoesNotExist:
                    pass
            if (self.cash_transfer_no or "").startswith("#") and self.approved: self.cash_transfer_no = self._generate_ct_number()
            super().save(*args, **kwargs)
            if self.approved and not old_approved: self._ensure_jv()

    class Meta:
        verbose_name = "Cash Transfer"
        verbose_name_plural = "Cash Transfers"
        constraints = [models.UniqueConstraint(fields=["cash_transfer_no"], name="uniq_cash_transfer_no_when_final", condition=~Q(cash_transfer_no__startswith="#"))]

class CashTransferItems(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)
    cash_transfer = models.ForeignKey(CashTransfer, on_delete=models.CASCADE, related_name="items", verbose_name="Cash Transfer")
    to_account = models.ForeignKey(BankAccounts, on_delete=models.CASCADE, related_name="cash_transfers_in", verbose_name="To Account")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)], verbose_name="Transfer Amount")
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    def __str__(self): return f"Transfer to {self.to_account.name} - Amount: {self.amount}"

    def clean(self):
        if self.cash_transfer and self.to_account and self.cash_transfer.from_account_id == self.to_account_id: raise ValidationError({"to_account": "Destination account must be different from source account."})
        if not self.to_account.gl_account: raise ValidationError({"to_account": "To Account must be linked to a GL account."})
        if self.cash_transfer and self.cash_transfer.approved: raise ValidationError("Cannot modify items of an approved Cash Transfer.")

    class Meta:
        verbose_name = "Cash Transfer Item"
        verbose_name_plural = "Cash Transfer Items"
