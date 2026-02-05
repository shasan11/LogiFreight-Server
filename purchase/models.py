# purchase/models.py
from __future__ import annotations

from decimal import Decimal
import uuid

from django.conf import settings
from django.db import models, transaction
from django.db.models import Q, Sum, F, DecimalField, ExpressionWrapper
from django.core.exceptions import ValidationError

from core.utils.coreModels import (
    TransactionBasedBranchScopedStampedOwnedActive,
    BranchScopedStampedOwnedActive,
    StampedOwnedActive,
)
from actors.models import Supplier

D0 = Decimal("0.00")


# -----------------------------
# Helpers for AP -> Operations
# -----------------------------

def _safe_decimal(v):
    return v if v is not None else D0


def _get_or_create_payment_summary_for_shipment(shipment):
    from operations.models import PaymentSummary
    ps, _ = PaymentSummary.objects.get_or_create(
        shipment=shipment,
        defaults={"branch": shipment.branch},
    )
    return ps


def _sync_vendor_bill_item_to_shipment_costing(vbi: "VendorBillItems"):
    if not vbi.shipment_id:
        return

    from operations.models import ShipmentCostings

    shipment = vbi.shipment
    ps = _get_or_create_payment_summary_for_shipment(shipment)

    qty = (vbi.qty or D0)
    base_unit = (vbi.rate or D0)

    # spread absolute taxes across units (simple + stable)
    per_unit_tax = D0
    if qty > 0:
        per_unit_tax = (vbi.taxes or D0) / qty

    effective_unit = (base_unit + per_unit_tax).quantize(Decimal("0.01"))

    defaults = dict(
        branch=shipment.branch,
        payment_summary=ps,
        actor="Vendor",
        payable_at="Origin",
        charge_name=(vbi.description or "Vendor Cost"),
        charge_type="Fixed",
        qty=qty if qty > 0 else Decimal("1.00"),
        tax_name=None,
        tax_rate=Decimal("0.00"),
        is_tax_exempt=True,
        reference_no=vbi.vendorbills.no if vbi.vendorbills_id else None,
        charge_currency=vbi.vendorbills.currency if vbi.vendorbills_id else None,
        invoice_currency=vbi.vendorbills.currency if vbi.vendorbills_id else None,
        exchange_rate=Decimal("1.000000"),
        unit_price_charge=effective_unit,
        unit_price_invoice=effective_unit,
        remarks=vbi.remarks,
        vendor_bill_item=vbi,
        expense_item=None,
    )

    ShipmentCostings.objects.update_or_create(
        vendor_bill_item=vbi,
        defaults=defaults,
    )

    ps.recompute_from_lines(save=True)


def _sync_expense_item_to_shipment_costing(ei: "ExpensesItems"):
    if not ei.shipment_id:
        return

    from operations.models import ShipmentCostings

    shipment = ei.shipment
    ps = _get_or_create_payment_summary_for_shipment(shipment)

    qty = (ei.quantity or D0)
    unit = (ei.rate or D0)

    defaults = dict(
        branch=shipment.branch,
        payment_summary=ps,
        actor="Vendor",
        payable_at="Origin",
        charge_name=(ei.description or "Expense Cost"),
        charge_type="Fixed",
        qty=qty if qty > 0 else Decimal("1.00"),
        tax_name=None,
        tax_rate=Decimal("0.00"),
        is_tax_exempt=True,
        reference_no=ei.expenses.exp_no if ei.expenses_id else None,
        charge_currency=ei.expenses.currency if ei.expenses_id else None,
        invoice_currency=ei.expenses.currency if ei.expenses_id else None,
        exchange_rate=Decimal("1.000000"),
        unit_price_charge=unit,
        unit_price_invoice=unit,
        remarks=None,
        vendor_bill_item=None,
        expense_item=ei,
    )

    ShipmentCostings.objects.update_or_create(
        expense_item=ei,
        defaults=defaults,
    )

    ps.recompute_from_lines(save=True)


# -----------------------------
# Models
# -----------------------------

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

    def recalc_total(self, save: bool = True):
        total = self.vendor_bills.filter(active=True).aggregate(s=Sum("total_amount")).get("s") or D0
        self.total_amount = total
        if save:
            self.save(update_fields=["total_amount"])


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
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("void", "Void"),
        ("paid", "Paid"),
        ("partially_paid", "Partially Paid"),
    ]

    exp_no = models.CharField(max_length=100, default="#DRAFT")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    invoice_reference = models.CharField(max_length=100, verbose_name="Invoice Reference")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="expenses_from_supplier", verbose_name="Supplier")
    expense_category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, verbose_name="Expense Category", blank=True, null=True)

    currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, related_name="currency_for_expenses", verbose_name="Currency")
    date = models.DateField(verbose_name="Invoice Date")
    due_date = models.DateField(verbose_name="Due Date")

    # OPTIONAL integration header link
    shipment = models.ForeignKey(
        "operations.Shipment",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="expenses",
    )

    subtotal_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Subtotal Amount")
    non_taxable_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Non-Taxable Amount")
    taxable_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Taxable Amount")
    discount_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Discount Amount")
    vat_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="VAT Amount")
    total_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Total Amount")

    paid_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Paid Amount")
    remaining_amount = models.DecimalField(default=D0, max_digits=18, decimal_places=2, verbose_name="Remaining Amount")

    paid_from = models.ForeignKey("accounting.ChartofAccounts", on_delete=models.PROTECT, related_name="expenses_paid_from", verbose_name="Paid From (Bank Account)")

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
            status = "approved" if getattr(self, "approved", False) else self.status
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

    # integration pointer (line-level)
    shipment = models.ForeignKey(
        "operations.Shipment",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="expense_items",
    )

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
        # inherit shipment from header if missing
        if not self.shipment_id and self.expenses_id and getattr(self.expenses, "shipment_id", None):
            self.shipment = self.expenses.shipment

        self.amount = (self.rate or D0) * (self.quantity or D0)

        super().save(*args, **kwargs)

        if self.expenses_id:
            self.expenses.recalc_from_items(save=True)
            self.expenses.update_status(save=True)

        transaction.on_commit(lambda: _sync_expense_item_to_shipment_costing(self))

    def delete(self, *args, **kwargs):
        from operations.models import ShipmentCostings

        parent = self.expenses
        pk = self.pk
        super().delete(*args, **kwargs)

        ShipmentCostings.objects.filter(expense_item_id=pk).delete()

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

    # OPTIONAL integration header link
    shipment = models.ForeignKey(
        "operations.Shipment",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="vendor_bills",
    )

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
            status = "approved" if getattr(self, "approved", False) else self.bill_status
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

    # integration pointer (line-level)
    shipment = models.ForeignKey(
        "operations.Shipment",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="vendor_bill_items",
    )

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
        # inherit branch + shipment from header if missing
        if not self.branch_id and self.vendorbills_id:
            self.branch = getattr(self.vendorbills, "branch", None)

        if not self.shipment_id and self.vendorbills_id and getattr(self.vendorbills, "shipment_id", None):
            self.shipment = self.vendorbills.shipment

        line_base = (self.rate or D0) * (self.qty or D0)
        self.total = max(D0, line_base + (self.taxes or D0) - (self.discount or D0))

        super().save(*args, **kwargs)

        if self.vendorbills_id:
            self.vendorbills.recalc_from_items(save=True)
            self.vendorbills.update_status(save=True)

        transaction.on_commit(lambda: _sync_vendor_bill_item_to_shipment_costing(self))

    def delete(self, *args, **kwargs):
        from operations.models import ShipmentCostings

        parent = self.vendorbills
        pk = self.pk
        super().delete(*args, **kwargs)

        ShipmentCostings.objects.filter(vendor_bill_item_id=pk).delete()

        if parent:
            parent.recalc_from_items(save=True)
            parent.update_status(save=True)


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
    paid_from = models.ForeignKey("accounting.ChartofAccounts", on_delete=models.PROTECT, related_name="vendorpayments_paid_from", verbose_name="Paid From (Bank Account)")
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
