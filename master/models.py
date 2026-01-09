from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords
import uuid
import re


# ---------------------------
# Units (Mass)
# ---------------------------
class UnitofMeasurement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    name = models.CharField(max_length=50, verbose_name="Unit Name")
    symbol = models.CharField(max_length=50, verbose_name="Unit Symbol")
    conversion_to_kg = models.DecimalField(verbose_name="Conversion to Kilogram", decimal_places=2, max_digits=10)
    active = models.BooleanField(default=True, verbose_name='Active')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    add_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT, related_name="un_add")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Unit of Measurement"
        indexes = [models.Index(fields=["name"]), models.Index(fields=["symbol"])]

    def __str__(self):
        return self.name

    def clean(self):
        if self.conversion_to_kg <= 0:
            raise ValidationError({"conversion_to_kg": "Conversion to Kilogram must be greater than 0."})


# ---------------------------
# Units (Length)
# ---------------------------
class UnitofMeasurementLength(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    name = models.CharField(max_length=50, verbose_name="Unit Name")
    symbol = models.CharField(max_length=50, verbose_name="Unit Symbol")
    conversion_to_cm = models.DecimalField(verbose_name="Conversion to Centi Meters", decimal_places=2, max_digits=10)
    active = models.BooleanField(default=True, verbose_name='Active')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT, related_name="unl_add")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Unit of Measurement (Length)"
        indexes = [models.Index(fields=["name"]), models.Index(fields=["symbol"])]

    def __str__(self):
        return self.name

    def clean(self):
        if self.conversion_to_cm <= 0:
            raise ValidationError({"conversion_to_cm": "Conversion to Centi Meters must be greater than 0."})


# ---------------------------
# Ports
# ---------------------------
class Ports(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    name = models.CharField(max_length=50, verbose_name="Port Name")
    symbol = models.CharField(max_length=50, verbose_name="Port Symbol")
    iso = models.CharField(max_length=50, verbose_name="ISO", blank=True, null=True)
    iata = models.CharField(max_length=50, verbose_name="IATA", blank=True, null=True)
    edi = models.CharField(max_length=50, verbose_name="EDI", blank=True, null=True)
    country = models.CharField(max_length=50, verbose_name="Country", blank=True, null=True)
    region = models.CharField(max_length=50, verbose_name="Region", blank=True, null=True)
    nearest_branch=models.ForeignKey('Branch', on_delete=models.PROTECT, blank=True, null=True, verbose_name="Nearest Branch")
    city = models.CharField(max_length=50, verbose_name="City", blank=True, null=True)
    is_land = models.BooleanField(default=True, verbose_name='Land')
    is_air = models.BooleanField(default=True, verbose_name='Air')
    is_sea = models.BooleanField(default=True, verbose_name='Sea')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Ports"
        indexes = [models.Index(fields=["name"]), models.Index(fields=["iso"]), models.Index(fields=["iata"])]

    def __str__(self):
        return self.name

    def clean(self):
        if not any([self.is_land, self.is_air, self.is_sea]):
            raise ValidationError("At least one of Land, Air, or Sea must be selected.")


# ---------------------------
# Branch
# ---------------------------
BRANCH_CODE_PREFIX = "BRANCH-"
BRANCH_CODE_RE = re.compile(rf"^{BRANCH_CODE_PREFIX}(\d+)$")


def _next_branch_number():
    last = Branch.objects.exclude(branch_id__isnull=True).exclude(branch_id__exact="").order_by("-created_at").first()
    if not last or not last.branch_id:
        return 300
    m = BRANCH_CODE_RE.match(last.branch_id)
    if not m:
        return 300
    return int(m.group(1)) + 1


def generate_branch_code():
    n = _next_branch_number()
    return f"{BRANCH_CODE_PREFIX}{n:08d}"


class Branch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)

    BRANCH_STATUS_CHOICES = [('operational', 'Operational'), ('closed', 'Closed'), ('under_construction', 'Under Construction')]

    branch_id = models.CharField(max_length=20, unique=True, verbose_name='Branch ID', blank=True, null=True, default=generate_branch_code)
    name = models.CharField(max_length=100, verbose_name='Branch Name')
    address = models.CharField(max_length=255, verbose_name='Address')
    city = models.CharField(max_length=100, verbose_name='City')
    state = models.CharField(max_length=100, verbose_name='State')
    country = models.CharField(max_length=100, verbose_name='Country')
    contact_number = models.CharField(max_length=15, verbose_name='Contact Number')
    status = models.CharField(max_length=20, choices=BRANCH_STATUS_CHOICES, default='operational', verbose_name='Status')
    established_date = models.DateField(verbose_name='Established Date', blank=True, null=True)
    is_main_branch = models.BooleanField(default=False, verbose_name='Is Main Branch')
    active = models.BooleanField(default=True, verbose_name='Active')
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT, related_name="user_branch_association")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.name} ({self.branch_id})"

    class Meta:
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'
        ordering = ['name']
        indexes = [models.Index(fields=['branch_id'], name='branch_id_idx'), models.Index(fields=['name'], name='branch_name_idx')]


# ---------------------------
# Master Data
# ---------------------------
MASTER_DATA_TYPE = [
    ("INCO", "INCO"),
    ("STATUS", "STATUS"),
    ("CONTAINER_TYPE", "CONTAINER_TYPE"),
    ("CARGO_TYPE", "CARGO_TYPE"),
    ("TRAILER_TYPE", "TRAILER_TYPE"),
    ("DELIVERY_TYPE", "DELIVERY_TYPE"),
    ("ShipmenSubType", "ShipmenSubTyp"),
    ("INCO", "INCO"),
]


class MasterData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    type_master = models.CharField(choices=MASTER_DATA_TYPE, max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    history = HistoricalRecords()

    class Meta:
        indexes = [models.Index(fields=["type_master", "name"])]

    def __str__(self):
        return f"{self.type_master} - {self.name}"


# ---------------------------
# Singleton: Application Settings
# ---------------------------
class ApplicationSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    name = models.CharField(max_length=255, default='My Logistics Company', blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    favicon = models.ImageField(upload_to='favicon/', blank=True, null=True)
    country = models.CharField(max_length=100, default='United States', blank=True, null=True)
    state = models.CharField(max_length=100, default='California', blank=True, null=True)
    address = models.TextField(default='123 Logistics Blvd, Suite 101, San Francisco, CA, 94101', blank=True, null=True)
    phone = models.CharField(max_length=20, verbose_name="Phone", default='+1 800 555 1234', blank=True, null=True)
    email = models.EmailField(blank=True, null=True, verbose_name="Email", default='info@logisticscompany.com')
    PAN = models.CharField(max_length=200, blank=True, null=True, verbose_name="PAN", default='ABCPQ1234D')

    def save(self, *args, **kwargs):
        if not self.pk and ApplicationSettings.objects.exists():
            raise ValidationError("Only one instance of this model is allowed.")
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Singleton Setting"
        verbose_name_plural = "Singleton Settings"

    def __str__(self):
        return self.name or "Application Settings"


# ---------------------------
# Singleton: Shipment Prefixes
# ---------------------------
class ShipmentPrefixes(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    shipment_prefix = models.CharField(max_length=20, default='SHIP', blank=True, null=True)
    journal_voucher_prefix = models.CharField(max_length=20, default='JV', blank=True, null=True)
    cash_transfer_prefix = models.CharField(max_length=20, default='CT', blank=True, null=True)
    payment_request_prefix = models.CharField(max_length=20, default='PAYREQ', blank=True, null=True)
    cheque_register_prefix = models.CharField(max_length=20, default='CR', blank=True, null=True)
    sales_prefix = models.CharField(max_length=20, default='SALE', blank=True, null=True)
    invoice_bundle_prefix = models.CharField(max_length=20, default='INVB', blank=True, null=True)
    batch_invoice_prefix = models.CharField(max_length=20, default='BINV', blank=True, null=True)
    customer_payment_prefix = models.CharField(max_length=20, default='CUSTPAY', blank=True, null=True)
    sales_return_prefix = models.CharField(max_length=20, default='SRET', blank=True, null=True)
    expense_category_prefix = models.CharField(max_length=20, default='EXPCAT', blank=True, null=True)
    supplier_prefix = models.CharField(max_length=20, default='SUP', blank=True, null=True)
    office_expense_prefix = models.CharField(max_length=20, default='OFFEXP', blank=True, null=True)
    expense_payment_prefix = models.CharField(max_length=20, default='EXPPAY', blank=True, null=True)
    vendor_bill_prefix = models.CharField(max_length=20, default='VBILL', blank=True, null=True)
    bill_bundle_prefix = models.CharField(max_length=20, default='BILLB', blank=True, null=True)
    master_job_prefix = models.CharField(max_length=20, default='MJOB', blank=True, null=True)
    booking_prefix = models.CharField(max_length=20, default='BOOK', blank=True, null=True)
    direct_order_prefix = models.CharField(max_length=20, default='DIRORD', blank=True, null=True)
    order_number_prefix = models.CharField(max_length=20, default='ORD', blank=True, null=True)
    vendor_payment_prefix = models.CharField(max_length=20, default='VPAY', blank=True, null=True)
    payment_return_prefix = models.CharField(max_length=20, default='PAYRET', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk and ShipmentPrefixes.objects.exists():
            raise ValidationError("Only one instance of this model is allowed.")
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Shipment Prefixes"
        verbose_name_plural = "Shipment Prefixes"

    def __str__(self):
        return "Shipment Prefix Configuration"
