# sales/models.py
from decimal import Decimal
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import Q
from django.utils import timezone
from accounting.models import BankAccounts, ChequeRegister, Currency
from actors.models import Customer
from master.models import Branch
from operations.models import Shipment,ShipmentTransportInfo
from core.utils.coreModels import BranchScopedStampedOwnedActive,TransactionBasedBranchScopedStampedOwnedActive


def generate_unique_no(prefix: str, model: models.Model, date_field: str = "created_at") -> str:
    today = timezone.localdate()
    today_str = today.strftime("%Y%m%d")
    field_name = date_field if hasattr(model, date_field) else "created_at"
    date_filter = {f"{field_name}__date": today}
    count_today = model.objects.filter(active=True, **date_filter).count() + 1
    return f"{prefix}-{today_str}-{count_today:04d}"


def _apply_vat_and_discount(base: Decimal, discount_percent: Decimal, vat_code: str) -> Decimal:
    base = base or Decimal("0")
    discount_percent = Decimal(discount_percent or 0)
    base_after_discount = base * (Decimal("1") - (discount_percent / Decimal("100")))
    if vat_code == "thirteen_vat":
        base_after_discount = base_after_discount * Decimal("1.13")
    return base_after_discount.quantize(Decimal("0.01"))



class Sales(TransactionBasedBranchScopedStampedOwnedActive):
    STATUS_CHOICES = [("pending", "Pending"), ("approved", "Approved"), ("void", "Void"), ("draft", "Draft")]
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    no = models.CharField(max_length=100, blank=True, null=True, default="#DRAFT")
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="sales_currency")
    reference = models.CharField(blank=True, null=True, max_length=35)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="sales")
    po_date = models.DateField(editable=True, verbose_name="PO Date")
    po_number = models.CharField(max_length=100, blank=True, null=True)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="shipment_sales", blank=True, null=True)
    to_be_paid_at=models.ForeignKey(ShipmentTransportInfo,on_delete=models.PROTECT,blank=True,null=True)
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    paid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
     

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["no"], name="uniq_sales_no_when_final", condition=~Q(no__startswith="#")),
            models.CheckConstraint(check=Q(total__gte=0), name="sales_total_non_negative"),
            models.CheckConstraint(check=Q(paid_amount__gte=0), name="sales_paid_non_negative"),
        ]
        indexes = [models.Index(fields=["no"]), models.Index(fields=["customer"])]

    def __str__(self):
        return f"Sale {self.no or self.id} - {self.customer}"

     

class SalesItem(models.Model):
    VAT_CHOICES = (("no_vat", "No Vat"), ("zero_vat", "0 Vat"), ("thirteen_vat", "13% VAT"))

    sales = models.ForeignKey(Sales, on_delete=models.CASCADE, related_name="items")
    item_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    rate = models.DecimalField(max_digits=10, decimal_places=2)
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
        return f"{self.item_name} (Sale {self.sales.id})"

    def _recompute_parent_total(self):
        total = Decimal("0.00")
        for item in self.sales.items.filter(active=True):
            base = Decimal(item.quantity) * (item.rate or Decimal("0"))
            total += _apply_vat_and_discount(base, item.discount_percent, item.vat)
        type(self.sales).objects.filter(pk=self.sales_id).update(total=total)

    def save(self, *args, **kwargs):
        base = Decimal(self.quantity or 0) * (self.rate or Decimal("0"))
        self.total = _apply_vat_and_discount(base, self.discount_percent, self.vat)
        discounted = base * (Decimal("1") - (Decimal(self.discount_percent or 0) / Decimal("100")))
        self.tax = (self.total - discounted).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)
        self._recompute_parent_total()

    def delete(self, *args, **kwargs):
        sale_id = self.sales_id
        super().delete(*args, **kwargs)
        sale = Sales.objects.filter(pk=sale_id).first()
        if sale:
            total = Decimal("0.00")
            for item in sale.items.filter(active=True):
                base = Decimal(item.quantity) * (item.rate or Decimal("0"))
                total += _apply_vat_and_discount(base, item.discount_percent, item.vat)
            Sales.objects.filter(pk=sale_id).update(total=total)


# ------------------------------------------------------------------------------
# Customer Payment
# ------------------------------------------------------------------------------
class CustomerPayment(TransactionBasedBranchScopedStampedOwnedActive):
    PAYMENT_TYPE_CHOICES = [("cash", "Cash"), ("bank", "Bank Transfer"), ("cheque", "Cheque")]
    STATUS_CHOICES = [("pending", "Pending"), ("approved", "Approved"), ("void", "Void"), ("draft", "Draft")]

    no = models.CharField(max_length=100, blank=True, null=True, default="#DRAFT")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="payments")
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="payment_currency")
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    customer_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
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

     


class CustomerPaymentItems(models.Model):
    no = models.CharField(max_length=100, blank=True, null=True, default="#DRAFT")
    customerpayment = models.ForeignKey(CustomerPayment, on_delete=models.CASCADE, related_name="customer_payment")
    sales = models.ForeignKey(Sales, on_delete=models.PROTECT, related_name="sales_customer_payment")
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
     

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["no"], name="uniq_payment_item_no_when_final", condition=~Q(no__startswith="#")),
            models.CheckConstraint(check=Q(allocated_amount__gte=0), name="cpitem_alloc_non_negative"),
        ]
        indexes = [models.Index(fields=["no"]), models.Index(fields=["sales"]), models.Index(fields=["customerpayment"])]

    def __str__(self):
        return f"Payment Item {self.no or self.id} → Sale {self.sales_id}"

    def clean(self):
        if self.customerpayment and self.sales and self.customerpayment.customer_id != self.sales.customer_id:
            raise ValidationError({"sales": "This sale belongs to a different customer than the payment."})

        if self.sales_id:
            active_items = self.sales.sales_customer_payment.filter(active=True)
            current_alloc = Decimal("0")
            if self.pk:
                try:
                    current_alloc = type(self).objects.get(pk=self.pk).allocated_amount or Decimal("0")
                except type(self).DoesNotExist:
                    current_alloc = Decimal("0")
            total_alloc_other = sum((i.allocated_amount or Decimal("0")) for i in active_items if i.pk != self.pk)
            outstanding = (self.sales.total or Decimal("0")) - total_alloc_other
            self.allocated_amount = self.allocated_amount or Decimal("0")
            if self.allocated_amount > outstanding + current_alloc:
                raise ValidationError({"allocated_amount": "Allocation exceeds outstanding amount for this sale."})

 
class SalesReturn(TransactionBasedBranchScopedStampedOwnedActive):
    STATUS_CHOICES = [("pending", "Pending"), ("approved", "Approved"), ("void", "Void"), ("draft", "Draft")]
    no = models.CharField(blank=True, null=True, max_length=100, default="#DRAFT")
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    client = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="clients_sales_return")
    inv_no = models.CharField(max_length=200, blank=True, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="sales_return_currency")
    reference_no = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["no"], name="uniq_salesreturn_no_when_final", condition=~Q(no__startswith="#")),
            models.CheckConstraint(check=Q(total__gte=0), name="sr_total_non_negative"),
        ]
        indexes = [models.Index(fields=["no"]), models.Index(fields=["client"])]

    def __str__(self):
        return f"Sales Return {self.no or self.id} - Invoice {self.inv_no or self.no}"

    def _recompute_total_from_items(self) -> Decimal:
        total_amount = Decimal("0.00")
        for item in self.items.filter(active=True):
            base = Decimal(item.quantity or 0) * (item.rate or Decimal("0"))
            total_amount += _apply_vat_and_discount(base, Decimal("0"), item.vat)
        type(self).objects.filter(pk=self.pk).update(total=total_amount)
        self.total = total_amount
        return total_amount

class SalesReturnItem(models.Model):
    VAT_CHOICES = [("no_vat", "No Vat"), ("zero_vat", "0 Vat"), ("thirteen_vat", "13% VAT")]

    sales_return = models.ForeignKey(SalesReturn, on_delete=models.CASCADE, related_name="items")
    item_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    vat = models.CharField(max_length=100, choices=VAT_CHOICES, default="no_vat")
    rate = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(quantity__gt=0), name="sri_qty_gt_zero"),
            models.CheckConstraint(check=Q(rate__gte=0), name="sri_rate_non_negative"),
        ]

    def __str__(self):
        return f"{self.item_name} (Return {self.sales_return.id})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.sales_return_id:
            self.sales_return._recompute_total_from_items()

    def delete(self, *args, **kwargs):
        sr_id = self.sales_return_id
        super().delete(*args, **kwargs)
        if sr_id:
            sr = SalesReturn.objects.filter(pk=sr_id).first()
            if sr:
                sr._recompute_total_from_items()
