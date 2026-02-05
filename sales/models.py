# sales/models.py
from __future__ import annotations

from decimal import Decimal
import uuid

from django.db import models
from django.db.models import Q, Sum
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounting.models import BankAccounts, ChequeRegister, Currency
from actors.models import Customer
from operations.models import Shipment, ShipmentTransportInfo, PaymentSummary
from core.utils.coreModels import BranchScopedStampedOwnedActive, TransactionBasedBranchScopedStampedOwnedActive


def generate_unique_no(prefix: str, model: type[models.Model], date_field: str = "created") -> str:
    today = timezone.localdate()
    today_str = today.strftime("%Y%m%d")
    field_name = date_field if hasattr(model, date_field) else "created"
    date_filter = {f"{field_name}__date": today}
    count_today = model.objects.filter(active=True, **date_filter).count() + 1
    return f"{prefix}-{today_str}-{count_today:04d}"


def _apply_vat_and_discount(base: Decimal, discount_percent: Decimal, vat_code: str) -> tuple[Decimal, Decimal, Decimal]:
    base = base or Decimal("0")
    discount_percent = Decimal(discount_percent or 0)

    net = base * (Decimal("1") - (discount_percent / Decimal("100")))
    net = net.quantize(Decimal("0.01"))

    vat_rate = Decimal("0")
    if vat_code == "thirteen_vat":
        vat_rate = Decimal("0.13")
    elif vat_code == "zero_vat":
        vat_rate = Decimal("0.00")
    else:
        vat_rate = Decimal("0.00")

    tax = (net * vat_rate).quantize(Decimal("0.01"))
    gross = (net + tax).quantize(Decimal("0.01"))
    return net, tax, gross


class Sales(TransactionBasedBranchScopedStampedOwnedActive):
    """
    Invoice (AR)
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("approved", "Approved/Posted"),
        ("partially_paid", "Partially Paid"),
        ("paid", "Paid"),
        ("void", "Void"),
    ]

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    no = models.CharField(max_length=100, blank=True, null=True, default="#DRAFT")
    invoice_date = models.DateField(default=timezone.localdate)

    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="sales_currency")
    reference = models.CharField(blank=True, null=True, max_length=120)

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="sales")

    po_date = models.DateField(editable=True, verbose_name="PO Date", default=timezone.localdate)
    po_number = models.CharField(max_length=100, blank=True, null=True)

    shipment = models.ForeignKey(Shipment, on_delete=models.SET_NULL, related_name="shipment_sales", blank=True, null=True)
    to_be_paid_at = models.ForeignKey(ShipmentTransportInfo, on_delete=models.PROTECT, blank=True, null=True)

    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="draft")

    paid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    class Meta:
        ordering = ["-created", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["no"], name="uniq_sales_no_when_final", condition=~Q(no__startswith="#")),
            models.CheckConstraint(check=Q(total__gte=0), name="sales_total_non_negative"),
            models.CheckConstraint(check=Q(paid_amount__gte=0), name="sales_paid_non_negative"),
            models.CheckConstraint(check=Q(balance_due__gte=0), name="sales_balance_non_negative"),
        ]
        indexes = [models.Index(fields=["no"]), models.Index(fields=["customer"])]

    def __str__(self):
        return f"Invoice {self.no or self.id} - {self.customer}"

    @transaction.atomic
    def finalize_number_if_needed(self, prefix="INV"):
        if self.no and not self.no.startswith("#"):
            return
        self.no = generate_unique_no(prefix, type(self), date_field="created")
        self.save(update_fields=["no"])

    def recompute_totals(self, save_self: bool = True) -> dict:
        agg = self.items.filter(active=True).aggregate(
            total=Sum("total"),
        )
        total = (agg["total"] or Decimal("0.00")).quantize(Decimal("0.01"))
        paid = (self.paid_amount or Decimal("0.00")).quantize(Decimal("0.01"))

        self.total = total
        self.paid_amount = paid
        self.balance_due = (total - paid).quantize(Decimal("0.01"))
        if self.balance_due < 0:
            self.balance_due = Decimal("0.00")

        if self.status != "void":
            if self.balance_due == Decimal("0.00") and total > 0:
                self.status = "paid"
            elif paid > 0 and self.balance_due > 0:
                self.status = "partially_paid"
            # if finalized number assigned (not draft), mark approved unless overridden
            elif self.status == "draft" and self.no and not self.no.startswith("#"):
                self.status = "approved"

        if save_self:
            type(self).objects.filter(pk=self.pk).update(
                total=self.total,
                paid_amount=self.paid_amount,
                balance_due=self.balance_due,
                status=self.status,
            )
        return {"total": self.total, "paid_amount": self.paid_amount, "balance_due": self.balance_due, "status": self.status}


class SalesItem(BranchScopedStampedOwnedActive):
    """
    Invoice lines.
    IMPORTANT CHANGE:
    - inherits BranchScopedStampedOwnedActive so it has active=True, branch, created/updated, etc.
    - quantity is DecimalField (freight needs decimals)
    """
    VAT_CHOICES = (("no_vat", "No Vat"), ("zero_vat", "0 Vat"), ("thirteen_vat", "13% VAT"))

    sales = models.ForeignKey(Sales, on_delete=models.CASCADE, related_name="items")

    # optional back-link (helps tracing and reporting)
    shipment_charge = models.ForeignKey(
        "operations.ShipmentCharges",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales_items",
    )

    item_name = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("1.00"))
    rate = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))

    vat = models.CharField(max_length=100, choices=VAT_CHOICES, default="no_vat")
    discount_percent = models.DecimalField(decimal_places=2, max_digits=12, default=0)

    tax = models.DecimalField(decimal_places=2, max_digits=12, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(quantity__gt=0), name="salesitem_qty_gt_zero"),
            models.CheckConstraint(check=Q(rate__gte=0), name="salesitem_rate_non_negative"),
            models.CheckConstraint(check=Q(discount_percent__gte=0), name="salesitem_discount_non_negative"),
        ]

    def __str__(self):
        return f"{self.item_name} (Invoice {self.sales_id})"

    def save(self, *args, **kwargs):
        base = (self.quantity or Decimal("0")) * (self.rate or Decimal("0"))
        net, tax, gross = _apply_vat_and_discount(base, self.discount_percent, self.vat)
        self.total = gross
        self.tax = tax
        super().save(*args, **kwargs)
        if self.sales_id:
            self.sales.recompute_totals(save_self=True)

    def delete(self, *args, **kwargs):
        sale_id = self.sales_id
        super().delete(*args, **kwargs)
        sale = Sales.objects.filter(pk=sale_id).first()
        if sale:
            sale.recompute_totals(save_self=True)


# -------------------------------------------------------------------
# Customer Receipt (Payment) + Allocation
# -------------------------------------------------------------------

class CustomerPayment(TransactionBasedBranchScopedStampedOwnedActive):
    PAYMENT_TYPE_CHOICES = [("cash", "Cash"), ("bank", "Bank Transfer"), ("cheque", "Cheque")]
    STATUS_CHOICES = [("draft", "Draft"), ("approved", "Approved"), ("void", "Void")]

    no = models.CharField(max_length=100, blank=True, null=True, default="#DRAFT")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="payments")
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="payment_currency")

    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="draft")

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    payment_reference_number = models.CharField(max_length=100, blank=True, null=True)
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPE_CHOICES, default="cash")

    bank_account = models.ForeignKey(BankAccounts, on_delete=models.SET_NULL, null=True, blank=True)
    cheque_register = models.ForeignKey(ChequeRegister, on_delete=models.SET_NULL, null=True, blank=True)

    desc = models.TextField(blank=True, null=True)
    pic = models.ImageField(upload_to="payments/", blank=True, null=True)

    class Meta:
        ordering = ["-date", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["no"], name="uniq_payment_no_when_final", condition=~Q(no__startswith="#")),
            models.CheckConstraint(check=Q(amount__gte=0), name="custpay_amount_non_negative"),
        ]
        indexes = [models.Index(fields=["no"]), models.Index(fields=["customer"])]

    def __str__(self):
        return f"Payment {self.no or self.id} - {self.customer}"

    def clean(self):
        if self.payment_type in ("cash", "bank") and not self.bank_account:
            raise ValidationError({"bank_account": "Bank account is required for cash/bank payments."})
        if self.payment_type == "cheque" and not self.cheque_register:
            raise ValidationError({"cheque_register": "Cheque register entry is required for cheque payments."})


class CustomerPaymentItems(BranchScopedStampedOwnedActive):
    """
    Allocation lines:
      CustomerPayment -> Sales
    """
    customerpayment = models.ForeignKey(CustomerPayment, on_delete=models.CASCADE, related_name="allocations")
    sales = models.ForeignKey(Sales, on_delete=models.PROTECT, related_name="sales_customer_payment")
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(check=Q(allocated_amount__gte=0), name="cpitem_alloc_non_negative"),
        ]
        indexes = [models.Index(fields=["sales"]), models.Index(fields=["customerpayment"])]

    def __str__(self):
        return f"Alloc {self.allocated_amount} → Invoice {self.sales_id}"

    def clean(self):
        if self.customerpayment_id and self.sales_id:
            if self.customerpayment.customer_id != self.sales.customer_id:
                raise ValidationError({"sales": "This invoice belongs to a different customer than the payment."})

            if self.customerpayment.currency_id != self.sales.currency_id:
                raise ValidationError({"sales": "Payment currency must match invoice currency (for now)."})

        # prevent over-allocation beyond invoice remaining
        if self.sales_id:
            inv = self.sales
            inv.recompute_totals(save_self=True)

            other_alloc = (
                type(self).objects.filter(active=True, sales_id=self.sales_id)
                .exclude(pk=self.pk)
                .aggregate(s=Sum("allocated_amount"))
                .get("s") or Decimal("0")
            )

            remaining = (inv.total or Decimal("0")) - (other_alloc or Decimal("0"))
            if (self.allocated_amount or Decimal("0")) > remaining:
                raise ValidationError({"allocated_amount": "Allocation exceeds remaining invoice amount."})

        # prevent over-allocation beyond receipt amount
        if self.customerpayment_id:
            other = (
                type(self).objects.filter(active=True, customerpayment_id=self.customerpayment_id)
                .exclude(pk=self.pk)
                .aggregate(s=Sum("allocated_amount"))
                .get("s") or Decimal("0")
            )
            if (other + (self.allocated_amount or Decimal("0"))) > (self.customerpayment.amount or Decimal("0")):
                raise ValidationError({"allocated_amount": "Allocation exceeds payment amount."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        _sync_invoice_and_shipment_paid_amounts(self.sales_id)

    def delete(self, *args, **kwargs):
        sid = self.sales_id
        super().delete(*args, **kwargs)
        _sync_invoice_and_shipment_paid_amounts(sid)


def _sync_invoice_and_shipment_paid_amounts(invoice_id: int) -> None:
    """
    After allocations change, update:
      - Sales.paid_amount + status/balance_due
      - PaymentSummary.paid_amount for that shipment
    """
    inv = Sales.objects.filter(pk=invoice_id).first()
    if not inv:
        return

    total_paid = (
        CustomerPaymentItems.objects.filter(active=True, sales_id=invoice_id)
        .aggregate(s=Sum("allocated_amount"))
        .get("s") or Decimal("0")
    )

    inv.paid_amount = Decimal(total_paid).quantize(Decimal("0.01"))
    inv.recompute_totals(save_self=True)

    if inv.shipment_id:
        ps = PaymentSummary.objects.filter(shipment_id=inv.shipment_id).first()
        if ps:
            ship_paid = (
                Sales.objects.filter(active=True, shipment_id=inv.shipment_id)
                .aggregate(s=Sum("paid_amount"))
                .get("s") or Decimal("0")
            )
            PaymentSummary.objects.filter(pk=ps.pk).update(paid_amount=Decimal(ship_paid).quantize(Decimal("0.01")))
