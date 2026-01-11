from decimal import Decimal
import uuid

from django.conf import settings
from django.db import models, transaction
from django.db.models import Q, Sum, F, DecimalField, ExpressionWrapper
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords

from core.utils.coreModels import TransactionBasedBranchScopedStampedOwnedActive, BranchScopedStampedOwnedActive, StampedOwnedActive
from actors.models import Supplier


D0 = Decimal("0.00")


class VendorBillsGroup(BranchScopedStampedOwnedActive):
    STATUS_CHOICES = [("pending", "Pending"), ("approved", "Approved"), ("void", "Void"), ("draft", "Draft")]

    no = models.CharField(max_length=100, blank=True, null=True, default="#DRAFT")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    total_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2)

    class Meta:
        ordering = ["-created", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["no"], name="uniq_vendorbillsgroup_no_when_final", condition=~Q(no__startswith="#")),
            models.CheckConstraint(check=Q(total_amount__gte=0), name="vendorbillsgroup_total_non_negative"),
        ]

    def __str__(self):
        return f"{self.no or '#DRAFT'} ({self.status})"


class ExpenseCategory(StampedOwnedActive):
    name = models.CharField(max_length=100, verbose_name="Category Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True, related_name="subcategories", verbose_name="Parent Category")

    class Meta:
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Expenses(BranchScopedStampedOwnedActive):
    STATUS_CHOICES = [("draft", "Draft"), ("pending", "Pending"), ("approved", "Approved"), ("void", "Void"), ("paid", "Paid"), ("partially_paid", "Partially Paid")]

    exp_no = models.CharField(max_length=100, default="#DRAFT")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    invoice_reference = models.CharField(max_length=100, verbose_name="Invoice Reference")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="expenses_from_supplier", verbose_name="Supplier")
    expense_category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, verbose_name="Expense Category", blank=True, null=True)
    currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, related_name="currency_for_expenses", verbose_name="Currency")
    date = models.DateField(verbose_name="Invoice Date")
    due_date = models.DateField(verbose_name="Due Date")

    subtotal_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Subtotal Amount")
    non_taxable_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Non-Taxable Amount")
    taxable_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Taxable Amount")
    discount_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Discount Amount")
    vat_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="VAT Amount")
    total_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Total Amount")

    paid_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Paid Amount")
    remaining_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Remaining Amount")

    paid_from = models.ForeignKey("accounting.Account", on_delete=models.PROTECT, related_name="expenses_paid_from", verbose_name="Paid From (Bank Account)")

    class Meta:
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"
        ordering = ("-date", "-id")
        constraints = [
            models.UniqueConstraint(fields=["exp_no"], name="uniq_expenses_no_when_final", condition=~Q(exp_no__startswith="#")),
            models.CheckConstraint(check=Q(total_amount__gte=0), name="expenses_total_non_negative"),
            models.CheckConstraint(check=Q(paid_amount__gte=0), name="expenses_paid_non_negative"),
            models.CheckConstraint(check=Q(remaining_amount__gte=0), name="expenses_remaining_non_negative"),
        ]

    def __str__(self):
        return self.exp_no or str(self.pk)

    def clean(self):
        if self.due_date and self.date and self.due_date < self.date:
            raise ValidationError({"due_date": "Due date cannot be earlier than invoice date."})

    def recalc_from_items(self, save: bool = True):
        agg = self.expenses_items.aggregate(
            subtotal=Sum("amount"),
            taxable=Sum("amount", filter=Q(vat_choices="13")),
            non_taxable=Sum("amount", filter=Q(vat_choices__in=["zero", "no_vat"])),
        )
        subtotal = agg["subtotal"] or D0
        taxable = agg["taxable"] or D0
        non_taxable = agg["non_taxable"] or D0
        total = (subtotal - (self.discount_amount or D0) + (self.vat_amount or D0))

        self.subtotal_amount = subtotal
        self.taxable_amount = taxable
        self.non_taxable_amount = non_taxable
        self.total_amount = total
        self.remaining_amount = max(D0, (self.total_amount or D0) - (self.paid_amount or D0))

        if save:
            self.save(update_fields=["subtotal_amount", "taxable_amount", "non_taxable_amount", "total_amount", "remaining_amount"])

    def update_status(self, save: bool = True):
        total = self.total_amount or D0
        paid = self.paid_amount or D0
        if total <= D0:
            status = self.status
        elif paid <= D0:
            status = "approved" if self.approved else self.status
        elif paid >= total:
            status = "paid"
        else:
            status = "partially_paid"
        if status != self.status:
            self.status = status
            if save:
                self.save(update_fields=["status"])


class ExpensesItems(models.Model):
    VAT_CHOICES = (("13", "13% VAT"), ("zero", "0% VAT"), ("no_vat", "No VAT"))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID")
    expenses = models.ForeignKey(Expenses, on_delete=models.CASCADE, related_name="expenses_items", verbose_name="Expense")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    rate = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Rate")
    quantity = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Quantity")
    amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Amount")
    vat_choices = models.CharField(max_length=100, choices=VAT_CHOICES, default="no_vat", verbose_name="VAT Type")

    class Meta:
        verbose_name = "Expense Item"
        verbose_name_plural = "Expense Items"
        ordering = ("id",)
        constraints = [
            models.CheckConstraint(check=Q(rate__gte=0), name="expensesitems_rate_non_negative"),
            models.CheckConstraint(check=Q(quantity__gte=0), name="expensesitems_qty_non_negative"),
            models.CheckConstraint(check=Q(amount__gte=0), name="expensesitems_amount_non_negative"),
        ]

    def __str__(self):
        return f"{self.expenses_id} - {self.amount}"

    def save(self, *args, **kwargs):
        self.amount = (self.rate or D0) * (self.quantity or D0)
        super().save(*args, **kwargs)
        if self.expenses_id:
            self.expenses.recalc_from_items(save=True)
            self.expenses.update_status(save=True)

    def delete(self, *args, **kwargs):
        parent = self.expenses
        super().delete(*args, **kwargs)
        if parent:
            parent.recalc_from_items(save=True)
            parent.update_status(save=True)


class VendorBills(TransactionBasedBranchScopedStampedOwnedActive):
    BILL_STATUS = [
        ("draft", "Draft"), ("pending", "Pending"), ("sent", "Sent"), ("due", "Due"), ("overdue", "Overdue"),
        ("partially_paid", "Partially Paid"), ("paid", "Paid"), ("processing", "Processing"),
        ("approved", "Approved"), ("rejected", "Rejected"), ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID")
    no = models.CharField(max_length=100, default="#DRAFT", blank=True, null=True, verbose_name="Bill No")
    vendor = models.ForeignKey("actors.Vendor", on_delete=models.PROTECT, related_name="vendor_bills", verbose_name="Vendor")
    invoice_reference = models.CharField(max_length=100, blank=True, null=True, verbose_name="Invoice Reference")
    date = models.DateField(verbose_name="Bill Date")
    due_date = models.DateField(verbose_name="Due Date")
    currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, related_name="currency_vendor_bills", verbose_name="Currency")
    vendor_bills_group = models.ForeignKey(VendorBillsGroup, on_delete=models.SET_NULL, blank=True, null=True, related_name="vendor_bills")

    subtotal_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Subtotal Amount")
    non_taxable_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Non-Taxable Amount")
    taxable_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Taxable Amount")
    discount_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Discount Amount")
    vat_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="VAT Amount")
    total_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Total Amount")

    paid_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Paid Amount")
    remaining_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Remaining Amount")

    bill_status = models.CharField(choices=BILL_STATUS, default="due", max_length=20, verbose_name="Bill Status")
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks")

    class Meta:
        verbose_name = "Vendor Bill"
        verbose_name_plural = "Vendor Bills"
        ordering = ("-date", "-id")
        constraints = [
            models.UniqueConstraint(fields=["no"], name="uniq_vendorbills_no_when_final", condition=~Q(no__startswith="#")),
            models.CheckConstraint(check=Q(total_amount__gte=0), name="vendorbills_total_non_negative"),
            models.CheckConstraint(check=Q(paid_amount__gte=0), name="vendorbills_paid_non_negative"),
            models.CheckConstraint(check=Q(remaining_amount__gte=0), name="vendorbills_remaining_non_negative"),
        ]

    def __str__(self):
        return self.no or str(self.pk)

    def clean(self):
        if self.due_date and self.date and self.due_date < self.date:
            raise ValidationError({"due_date": "Due date cannot be earlier than bill date."})

    def recalc_from_items(self, save: bool = True):
        agg = self.bill_items.aggregate(
            subtotal=Sum(ExpressionWrapper(F("rate") * F("qty"), output_field=DecimalField(max_digits=18, decimal_places=2))),
            discount=Sum("discount"),
            taxes=Sum("taxes"),
            total=Sum("total"),
            taxable=Sum("total", filter=Q(vat_choices="13")),
            non_taxable=Sum("total", filter=Q(vat_choices__in=["zero", "no_vat"])),
        )
        self.subtotal_amount = agg["subtotal"] or D0
        self.discount_amount = agg["discount"] or D0
        self.vat_amount = agg["taxes"] or D0
        self.total_amount = agg["total"] or D0
        self.taxable_amount = agg["taxable"] or D0
        self.non_taxable_amount = agg["non_taxable"] or D0
        self.remaining_amount = max(D0, (self.total_amount or D0) - (self.paid_amount or D0))

        if save:
            self.save(update_fields=["subtotal_amount", "discount_amount", "vat_amount", "total_amount", "taxable_amount", "non_taxable_amount", "remaining_amount"])

        if self.vendor_bills_group_id:
            self.vendor_bills_group.recalc_total(save=True)

    def update_status(self, save: bool = True):
        total = self.total_amount or D0
        paid = self.paid_amount or D0
        if total <= D0:
            status = self.bill_status
        elif paid <= D0:
            status = "approved" if self.approved else self.bill_status
        elif paid >= total:
            status = "paid"
        else:
            status = "partially_paid"
        if status != self.bill_status:
            self.bill_status = status
            if save:
                self.save(update_fields=["bill_status"])


class VendorBillItems(models.Model):
    VAT_CHOICES = (("13", "13% VAT"), ("zero", "0% VAT"), ("no_vat", "No VAT"))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendorbills = models.ForeignKey(VendorBills, on_delete=models.CASCADE, related_name="bill_items", verbose_name="Vendor Bill")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    rate = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Rate")
    qty = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Quantity")
    taxes = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Taxes")
    discount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Discount")
    vat_choices = models.CharField(max_length=100, choices=VAT_CHOICES, default="no_vat", verbose_name="VAT Type")
    total = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Line Total")
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks")
    branch = models.ForeignKey("master.Branch", on_delete=models.PROTECT, verbose_name="Branch", related_name="vendor_bill_item_branch", blank=True, null=True)

    class Meta:
        verbose_name = "Vendor Bill Item"
        verbose_name_plural = "Vendor Bill Items"
        ordering = ("id",)
        constraints = [
            models.CheckConstraint(check=Q(rate__gte=0), name="vendorbillitems_rate_non_negative"),
            models.CheckConstraint(check=Q(qty__gte=0), name="vendorbillitems_qty_non_negative"),
            models.CheckConstraint(check=Q(taxes__gte=0), name="vendorbillitems_taxes_non_negative"),
            models.CheckConstraint(check=Q(discount__gte=0), name="vendorbillitems_discount_non_negative"),
            models.CheckConstraint(check=Q(total__gte=0), name="vendorbillitems_total_non_negative"),
        ]

    def save(self, *args, **kwargs):
        line_base = (self.rate or D0) * (self.qty or D0)
        self.total = max(D0, line_base + (self.taxes or D0) - (self.discount or D0))
        super().save(*args, **kwargs)
        if self.vendorbills_id:
            self.vendorbills.recalc_from_items(save=True)
            self.vendorbills.update_status(save=True)

    def delete(self, *args, **kwargs):
        parent = self.vendorbills
        super().delete(*args, **kwargs)
        if parent:
            parent.recalc_from_items(save=True)
            parent.update_status(save=True)


def _group_recalc_total(group_id):
    from django.apps import apps
    VendorBills = apps.get_model("your_app_name_here", "VendorBills")  # replace app label if you want to call this helper
    return VendorBills.objects.filter(vendor_bills_group_id=group_id).aggregate(s=Sum("total_amount"))["s"] or D0


def _safe_decimal(v):
    return v if v is not None else D0


def _recalc_vendor_bill_paid(bill: VendorBills):
    agg = bill.bill_payment_entries.aggregate(s=Sum("amount"))
    bill.paid_amount = agg["s"] or D0
    bill.remaining_amount = max(D0, _safe_decimal(bill.total_amount) - _safe_decimal(bill.paid_amount))
    bill.save(update_fields=["paid_amount", "remaining_amount"])
    bill.update_status(save=True)


class VendorPayments(TransactionBasedBranchScopedStampedOwnedActive):
    STATUS = [
        ("draft", "Draft"), ("pending", "Pending"), ("approved", "Approved"), ("void", "Void"),
        ("processing", "Processing"), ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID")
    no = models.CharField(max_length=100, default="#DRAFT", blank=True, null=True, verbose_name="Payment No")
    vendor = models.ForeignKey("actors.Vendor", on_delete=models.PROTECT, related_name="vendor_payments", verbose_name="Vendor")
    paid_from = models.ForeignKey("accounting.Account", on_delete=models.PROTECT, related_name="vendorpayments_paid_from", verbose_name="Paid From (Bank Account)")
    date = models.DateField(verbose_name="Payment Date")
    remarks = models.TextField(blank=True, null=True, verbose_name="Reference/Remarks")
    currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, related_name="currency_vendor_payments", verbose_name="Currency")
    amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Amount")
    bank_charges = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Bank Charges")
    tds_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="TDS Amount")
    tds_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="TDS Type")
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    class Meta:
        verbose_name = "Vendor Payment"
        verbose_name_plural = "Vendor Payments"
        ordering = ("-date", "-id")
        constraints = [
            models.UniqueConstraint(fields=["no"], name="uniq_vendorpayments_no_when_final", condition=~Q(no__startswith="#")),
            models.CheckConstraint(check=Q(amount__gte=0), name="vendorpayments_amount_non_negative"),
        ]

    def __str__(self):
        return self.no or str(self.pk)

    def recalc_amount(self, save: bool = True):
        agg = self.payment_entries.aggregate(s=Sum("amount"))
        self.amount = agg["s"] or D0
        if save:
            self.save(update_fields=["amount"])


class VendorPaymentEntries(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID")
    vendor_payments = models.ForeignKey(VendorPayments, on_delete=models.CASCADE, related_name="payment_entries", verbose_name="Vendor Payment")
    vendor_bills = models.ForeignKey(VendorBills, on_delete=models.PROTECT, related_name="bill_payment_entries", verbose_name="Vendor Bill")
    amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Applied Amount")
    branch = models.ForeignKey("master.Branch", on_delete=models.PROTECT, verbose_name="Branch", related_name="vendor_payment_entries_branch", blank=True, null=True)

    class Meta:
        verbose_name = "Vendor Payment Entry"
        verbose_name_plural = "Vendor Payment Entries"
        ordering = ("id",)
        constraints = [models.CheckConstraint(check=Q(amount__gte=0), name="vendorpaymententries_amount_non_negative")]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.vendor_payments_id:
            self.vendor_payments.recalc_amount(save=True)
        if self.vendor_bills_id:
            _recalc_vendor_bill_paid(self.vendor_bills)

    def delete(self, *args, **kwargs):
        vp = self.vendor_payments
        vb = self.vendor_bills
        super().delete(*args, **kwargs)
        if vp:
            vp.recalc_amount(save=True)
        if vb:
            _recalc_vendor_bill_paid(vb)


class PurchaseReturn(TransactionBasedBranchScopedStampedOwnedActive):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    no = models.CharField(max_length=100, blank=True, null=True, default="#DRAFT")
    vendor = models.ForeignKey("actors.Vendor", on_delete=models.PROTECT, related_name="vendor_purchase_return")
    inv_no = models.CharField(max_length=200, blank=True, null=True)
    currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, related_name="purchase_return_currency")
    reference_no = models.CharField(max_length=100, blank=True, null=True)
    

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(fields=["no"], name="uniq_purchase_return_no_when_final", condition=~Q(no__startswith="#")),
            models.CheckConstraint(check=Q(total__gte=0), name="purchase_return_total_non_negative"),
        ]

    def __str__(self):
        return self.no or str(self.pk)

    def recalc_total(self, save: bool = True):
        agg = self.items.aggregate(s=Sum("total"))
        self.total = agg["s"] or D0
        if save:
            self.save(update_fields=["total"])


class PurchaseReturnItem(models.Model):
    VAT_CHOICES = (("no_vat", "No VAT"), ("zero_vat", "0% VAT"), ("thirteen_vat", "13% VAT"))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    total = models.DecimalField(max_digits=20, decimal_places=2, default=D0)
    purchase_return = models.ForeignKey(PurchaseReturn, on_delete=models.CASCADE, related_name="items")
    item_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    vat = models.CharField(max_length=100, default="no_vat", choices=VAT_CHOICES)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    

    class Meta:
        ordering = ("id",)
        constraints = [models.CheckConstraint(check=Q(total__gte=0), name="purchase_return_item_total_non_negative")]

    def save(self, *args, **kwargs):
        self.total = Decimal(self.quantity or 0) * (self.rate or D0)
        super().save(*args, **kwargs)
        if self.purchase_return_id:
            self.purchase_return.recalc_total(save=True)

    def delete(self, *args, **kwargs):
        pr = self.purchase_return
        super().delete(*args, **kwargs)
        if pr:
            pr.recalc_total(save=True)


class ExpensePayments(TransactionBasedBranchScopedStampedOwnedActive):
    STATUS = [("draft", "Draft"), ("pending", "Pending"), ("approved", "Approved"), ("void", "Void")]

    no = models.CharField(max_length=100, default="#DRAFT", blank=True, null=True, verbose_name="Payment No")
    paid_from = models.ForeignKey("accounting.Account", on_delete=models.PROTECT, related_name="expense_payments_paid_from", verbose_name="Paid From (Bank Account)")
    date = models.DateField(verbose_name="Payment Date")
    remarks = models.TextField(blank=True, null=True, verbose_name="Reference/Remarks")
    due_date = models.DateField(blank=True, null=True, verbose_name="Due Date")
    currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, related_name="expense_payments_currency", verbose_name="Currency")
    amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Amount")
    bank_charges = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Bank Charges")
    tds_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="TDS Amount")
    tds_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="TDS Type")
    status = models.CharField(max_length=20, choices=STATUS, default="pending")

    class Meta:
        verbose_name = "Expense Payment"
        verbose_name_plural = "Expense Payments"
        ordering = ("-date", "-id")
        constraints = [
            models.UniqueConstraint(fields=["no"], name="uniq_expensepayments_no_when_final", condition=~Q(no__startswith="#")),
            models.CheckConstraint(check=Q(amount__gte=0), name="expensepayments_amount_non_negative"),
        ]

    def __str__(self):
        return self.no or str(self.pk)

    def recalc_amount(self, save: bool = True):
        agg = self.payment_entries.aggregate(s=Sum("amount"))
        self.amount = agg["s"] or D0
        if save:
            self.save(update_fields=["amount"])


def _recalc_expense_paid(exp: Expenses):
    agg = exp.expense_payment_entries.aggregate(s=Sum("amount"))
    exp.paid_amount = agg["s"] or D0
    exp.remaining_amount = max(D0, _safe_decimal(exp.total_amount) - _safe_decimal(exp.paid_amount))
    exp.save(update_fields=["paid_amount", "remaining_amount"])
    exp.update_status(save=True)


class ExpensePaymentEntries(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID")
    expense_payments = models.ForeignKey(ExpensePayments, on_delete=models.CASCADE, related_name="payment_entries", verbose_name="Expense Payment")
    expenses = models.ForeignKey(Expenses, on_delete=models.PROTECT, related_name="expense_payment_entries", verbose_name="Expense")
    amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Applied Amount")
    branch = models.ForeignKey("master.Branch", on_delete=models.PROTECT, verbose_name="Branch", related_name="expense_payment_entries_branch", blank=True, null=True)

    class Meta:
        verbose_name = "Expense Payment Entry"
        verbose_name_plural = "Expense Payment Entries"
        ordering = ("id",)
        constraints = [models.CheckConstraint(check=Q(amount__gte=0), name="expensepaymententries_amount_non_negative")]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.expense_payments_id:
            self.expense_payments.recalc_amount(save=True)
        if self.expenses_id:
            _recalc_expense_paid(self.expenses)

    def delete(self, *args, **kwargs):
        ep = self.expense_payments
        exp = self.expenses
        super().delete(*args, **kwargs)
        if ep:
            ep.recalc_amount(save=True)
        if exp:
            _recalc_expense_paid(exp)
