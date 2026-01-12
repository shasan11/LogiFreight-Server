from __future__ import annotations

from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone
from django.core.validators import MinValueValidator
from master.models import UnitofMeasurement, UnitofMeasurementLength
from core.utils.coreModels import BranchScopedStampedOwnedActive, UUIDPk
from django.db.models import Q


def _seq_key(prefix: str, branch_id: int | None) -> str:
    return f"{prefix}:{branch_id or 'NA'}"


class LocalSequence(UUIDPk):
    key = models.CharField(max_length=80, unique=True)
    last_value = models.PositiveBigIntegerField(default=0)

    @classmethod
    def next(cls, key: str) -> int:
        with transaction.atomic():
            obj, _ = cls.objects.select_for_update().get_or_create(key=key)
            obj.last_value += 1
            obj.save(update_fields=["last_value"])
            return int(obj.last_value)

    def __str__(self) -> str:
        return f"{self.key}={self.last_value}"

class ContactGroup(BranchScopedStampedOwnedActive):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=30, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "name"],
                name="uq_contactgroup_branch_name",
            ),
            models.UniqueConstraint(
                fields=["branch", "code"],
                condition=~Q(code__isnull=True) & ~Q(code=""),
                name="uq_contactgroup_branch_code",
            ),
        ]
        indexes = [
            models.Index(fields=["branch", "name"]),
            models.Index(fields=["branch", "code"]),
        ]

    def __str__(self):
        return self.name


class Contact(BranchScopedStampedOwnedActive):
    TYPE_CHOICES = [
        ("customer", "Customer"),
        ("supplier", "Supplier"),
        ("consignee", "Consignee"),
        ("shipper", "Shipper"),
        ("agent", "Agent"),
        ("carrier", "Carrier"),
        ("other", "Other"),
    ]

    type = models.CharField(max_length=30, choices=TYPE_CHOICES, default="customer")

    code = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=180)
    legal_name = models.CharField(max_length=220, null=True, blank=True)

    phone = models.CharField(max_length=40, null=True, blank=True)
    phone_alt = models.CharField(max_length=40, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)

    country = models.CharField(max_length=80, null=True, blank=True)
    state = models.CharField(max_length=80, null=True, blank=True)
    city = models.CharField(max_length=80, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    tax_id = models.CharField(max_length=80, null=True, blank=True)
    credit_limit = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    notes = models.TextField(null=True, blank=True)

    groups = models.ManyToManyField(
        ContactGroup,
        blank=True,
        related_name="contacts",
    )

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "code"],
                condition=~Q(code__isnull=True) & ~Q(code=""),
                name="uq_contact_branch_code",
            ),
        ]
        indexes = [
            models.Index(fields=["branch", "name"]),
            models.Index(fields=["branch", "email"]),
            models.Index(fields=["branch", "phone"]),
            models.Index(fields=["branch", "type"]),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if not self.name or not self.name.strip():
            raise ValidationError({"name": "Name is required."})

        # Optional sanity: keep email lowercase if provided
        if self.email:
            self.email = self.email.strip().lower()

        # Optional: if code is given, strip spaces
        if self.code:
            self.code = self.code.strip()

        super().clean()

class Lead(BranchScopedStampedOwnedActive):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        CONTACTED = "CONTACTED", "Contacted"
        QUALIFIED = "QUALIFIED", "Qualified"
        PROPOSAL = "PROPOSAL", "Proposal/Quotation"
        NEGOTIATION = "NEGOTIATION", "Negotiation"
        WON = "WON", "Won"
        LOST = "LOST", "Lost"
        CLOSED = "CLOSED", "Closed"

    class Source(models.TextChoices):
        WALK_IN = "WALK_IN", "Walk-in"
        WEBSITE = "WEBSITE", "Website"
        REFERRAL = "REFERRAL", "Referral"
        COLD_CALL = "COLD_CALL", "Cold Call"
        EMAIL = "EMAIL", "Email"
        WHATSAPP = "WHATSAPP", "WhatsApp"
        FACEBOOK = "FACEBOOK", "Facebook"
        LINKEDIN = "LINKEDIN", "LinkedIn"
        PARTNER = "PARTNER", "Partner"
        OTHER = "OTHER", "Other"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    lead_no = models.CharField(max_length=40, unique=True, db_index=True, editable=False)
    title = models.CharField(max_length=160, blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.OTHER)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_leads", blank=True, null=True)
    customer = models.ForeignKey("crm.Contact", on_delete=models.PROTECT, related_name="leads", blank=True, null=True)
    company_name = models.CharField(max_length=160, blank=True, null=True)
    contact_name = models.CharField(max_length=120, blank=True, null=True)
    phone = models.CharField(max_length=40, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    origin_port = models.CharField(max_length=64, blank=True, null=True)
    destination_port = models.CharField(max_length=64, blank=True, null=True)
    direction = models.CharField(max_length=10, blank=True, null=True)
    transportation_mode = models.CharField(max_length=10, blank=True, null=True)
    incoterms = models.CharField(max_length=10, blank=True, null=True)
    expected_close_date = models.DateField(blank=True, null=True)
    estimated_value = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    estimated_currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, related_name="+", blank=True, null=True)
    probability = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    last_contacted_at = models.DateTimeField(blank=True, null=True)
    next_follow_up_at = models.DateTimeField(blank=True, null=True)
    lost_reason = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self) -> str:
        return self.lead_no

    def _ensure_lead_no(self):
        if self.lead_no:
            return
        key = _seq_key("LEAD", getattr(self, "branch_id", None))
        seq = LocalSequence.next(key)
        self.lead_no = f"LED-{seq:08d}"

    def save(self, *args, **kwargs):
        self._ensure_lead_no()
        self.full_clean()
        return super().save(*args, **kwargs)


class LeadActivity(BranchScopedStampedOwnedActive):
    class Type(models.TextChoices):
        CALL = "CALL", "Call"
        EMAIL = "EMAIL", "Email"
        MEETING = "MEETING", "Meeting"
        WHATSAPP = "WHATSAPP", "WhatsApp"
        NOTE = "NOTE", "Note"
        TASK = "TASK", "Task"
        OTHER = "OTHER", "Other"

    class Outcome(models.TextChoices):
        NO_ANSWER = "NO_ANSWER", "No Answer"
        CONNECTED = "CONNECTED", "Connected"
        INTERESTED = "INTERESTED", "Interested"
        NOT_INTERESTED = "NOT_INTERESTED", "Not Interested"
        FOLLOW_UP = "FOLLOW_UP", "Follow Up Needed"
        QUOTE_REQUESTED = "QUOTE_REQUESTED", "Quotation Requested"
        QUOTE_SENT = "QUOTE_SENT", "Quotation Sent"
        WON = "WON", "Won"
        LOST = "LOST", "Lost"
        OTHER = "OTHER", "Other"

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=20, choices=Type.choices, default=Type.CALL)
    outcome = models.CharField(max_length=30, choices=Outcome.choices, default=Outcome.OTHER)
    subject = models.CharField(max_length=160, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    activity_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="lead_activities", blank=True, null=True)

    class Meta:
        ordering = ["-activity_at", "-created"]

    def __str__(self) -> str:
        return f"{self.lead_id} {self.activity_type} {self.activity_at}"


class LeadFollowUp(BranchScopedStampedOwnedActive):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        DONE = "DONE", "Done"
        MISSED = "MISSED", "Missed"
        CANCELLED = "CANCELLED", "Cancelled"

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="follow_ups")
    due_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    channel = models.CharField(max_length=40, blank=True, null=True)
    agenda = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="lead_followups", blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["status", "due_at", "-created"]

    def __str__(self) -> str:
        return f"{self.lead_id} {self.status} {self.due_at}"


class Quotation(BranchScopedStampedOwnedActive):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SENT = "SENT", "Sent"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        EXPIRED = "EXPIRED", "Expired"
        CANCELLED = "CANCELLED", "Cancelled"

    class TransportationMode(models.TextChoices):
        AIR = "air", "Air"
        OCEAN = "ocean", "Ocean"
        LAND = "land", "Land"

    class ShippingMode(models.TextChoices):
        HOUSE = "house", "House"
        DIRECT = "direct", "Direct"

    class Direction(models.TextChoices):
        EXPORT = "export", "Export"
        IMPORT = "import", "Import"

    class UnitType(models.TextChoices):
        SI_METRIC = "si_metric", "SI (Metric)"
        IMPERIAL = "imperial", "Imperial"

    class Incoterms(models.TextChoices):
        EXW = "EXW", "EXW"
        FCA = "FCA", "FCA"
        FOB = "FOB", "FOB"
        CFR = "CFR", "CFR"
        CIF = "CIF", "CIF"
        CPT = "CPT", "CPT"
        CIP = "CIP", "CIP"
        DAP = "DAP", "DAP"
        DDP = "DDP", "DDP"

    quote_no = models.CharField(max_length=40, unique=True, db_index=True, editable=False)
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, related_name="quotations", blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    transportation_mode = models.CharField(max_length=10, choices=TransportationMode.choices, default=TransportationMode.AIR)
    shipping_mode = models.CharField(max_length=10, choices=ShippingMode.choices, default=ShippingMode.HOUSE)
    direction = models.CharField(max_length=10, choices=Direction.choices, default=Direction.EXPORT)
    port_of_departure = models.CharField(max_length=64, blank=True, null=True)
    port_of_arrival = models.CharField(max_length=64, blank=True, null=True)
    transit_time_days = models.PositiveIntegerField(blank=True, null=True)
    carrier = models.CharField(max_length=120, blank=True, null=True)
    delivery_point = models.CharField(max_length=120, blank=True, null=True)
    place_of_receipt = models.CharField(max_length=120, blank=True, null=True)
    incoterms = models.CharField(max_length=10, choices=Incoterms.choices, blank=True, null=True)
    issued_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(blank=True, null=True)
    doc_ref_no = models.CharField(max_length=120, blank=True, null=True)
    payment_terms_days = models.PositiveIntegerField(blank=True, null=True)
    unit_type = models.CharField(max_length=20, choices=UnitType.choices, default=UnitType.SI_METRIC)
    salesman = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="quotations", blank=True, null=True)
    shipper = models.ForeignKey("crm.Contact", on_delete=models.PROTECT, related_name="shipper_quotations", blank=True, null=True)
    consignee = models.ForeignKey("crm.Contact", on_delete=models.PROTECT, related_name="consignee_quotations", blank=True, null=True)
    client = models.ForeignKey("crm.Contact", on_delete=models.PROTECT, related_name="client_quotations", blank=True, null=True)
    contact_person_name = models.CharField(max_length=120, blank=True, null=True)
    contact_person_phone = models.CharField(max_length=40, blank=True, null=True)
    contact_person_email = models.EmailField(blank=True, null=True)
    contact_person_address = models.TextField(blank=True, null=True)
    terms_and_conditions = models.TextField(blank=True, null=True)
    charge_currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, related_name="+", blank=True, null=True)
    invoice_currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, related_name="+", blank=True, null=True)
    exchange_rate = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("1.000000"))
    subtotal_charge = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    tax_total_charge = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    total_charge = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    subtotal_invoice = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    tax_total_invoice = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    total_invoice = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    converted_shipment = models.OneToOneField("operations.Shipment", on_delete=models.SET_NULL, related_name="from_quotation", blank=True, null=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self) -> str:
        return self.quote_no

    def clean(self):
        if self.exchange_rate is None or self.exchange_rate <= 0:
            raise ValidationError({"exchange_rate": "Exchange rate must be > 0."})
        if self.expiry_date and self.issued_date and self.expiry_date < self.issued_date:
            raise ValidationError({"expiry_date": "Expiry must be after issued date."})

    def _ensure_quote_no(self):
        if self.quote_no:
            return
        key = _seq_key("QUOTATION", getattr(self, "branch_id", None))
        seq = LocalSequence.next(key)
        self.quote_no = f"QTN-{seq:08d}"

    def recompute_totals(self):
        agg = self.charge_lines.aggregate(
            subtotal_charge=Sum("subtotal_charge"),
            tax_total_charge=Sum("tax_amount_charge"),
            total_charge=Sum("total_with_tax_charge"),
            subtotal_invoice=Sum("subtotal_invoice"),
            tax_total_invoice=Sum("tax_amount_invoice"),
            total_invoice=Sum("total_with_tax_invoice"),
        )
        self.subtotal_charge = agg["subtotal_charge"] or Decimal("0.00")
        self.tax_total_charge = agg["tax_total_charge"] or Decimal("0.00")
        self.total_charge = agg["total_charge"] or Decimal("0.00")
        self.subtotal_invoice = agg["subtotal_invoice"] or Decimal("0.00")
        self.tax_total_invoice = agg["tax_total_invoice"] or Decimal("0.00")
        self.total_invoice = agg["total_invoice"] or Decimal("0.00")

    def save(self, *args, **kwargs):
        self._ensure_quote_no()
        self.full_clean()
        return super().save(*args, **kwargs)


class QuotationDocument(BranchScopedStampedOwnedActive):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="documents")
    document = models.FileField(upload_to="quotation_documents/%Y/%m/")
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self) -> str:
        return f"Doc {self.id} for {self.quotation_id}"


class QuotationNote(BranchScopedStampedOwnedActive):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="notes")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self) -> str:
        return f"Note {self.title} ({self.quotation_id})"


class QuotationPackage(BranchScopedStampedOwnedActive):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="packages")
    good_desc = models.CharField(max_length=120, blank=True, null=True)
    country_of_origin = models.CharField(max_length=80, blank=True, null=True)
    fragile = models.BooleanField(default=False)
    hs_code = models.CharField(max_length=50, blank=True, null=True)
    length = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    package_unit = models.ForeignKey(UnitofMeasurementLength, on_delete=models.PROTECT, related_name="quotation_pkg_unit_length")
    gross_weight = models.FloatField(blank=True, null=True)
    mass_unit = models.ForeignKey(UnitofMeasurement, on_delete=models.PROTECT, related_name="quotation_pkg_unit_mass", blank=True, null=True)
    quantity = models.PositiveBigIntegerField(default=1)
    volumetric_weight = models.FloatField(blank=True, null=True, default=0)
    chargeable_weight = models.FloatField(blank=True, null=True, default=0)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self) -> str:
        return str(self.good_desc or f"Pkg {self.id}")


class QuotationLineBase(models.Model):
    class PayableAt(models.TextChoices):
        ORIGIN = "Origin", "Origin"
        DESTINATION = "Destination", "Destination"

    class Actor(models.TextChoices):
        CUSTOMER = "Customer", "Customer"
        AGENT = "Agent", "Agent"
        CARRIER = "Carrier", "Carrier"
        VENDOR = "Vendor", "Vendor"

    payable_at = models.CharField(max_length=20, choices=PayableAt.choices, default=PayableAt.ORIGIN)
    actor = models.CharField(max_length=30, choices=Actor.choices, default=Actor.CUSTOMER)
    applied_to = models.ForeignKey("crm.Contact", on_delete=models.PROTECT, null=True, blank=True)
    charge_name = models.CharField(max_length=120)
    charge_type = models.CharField(max_length=50, default="Fixed")
    qty = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("1.00"))
    tax_name = models.CharField(max_length=100, blank=True, null=True)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    is_tax_exempt = models.BooleanField(default=False)
    remarks = models.TextField(blank=True, null=True)
    reference_no = models.CharField(max_length=120, blank=True, null=True)
    charge_currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    invoice_currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("1.000000"))
    unit_price_charge = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    subtotal_charge = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    tax_amount_charge = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    total_with_tax_charge = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    unit_price_invoice = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    subtotal_invoice = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    tax_amount_invoice = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    total_with_tax_invoice = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def clean(self):
        if self.is_tax_exempt:
            self.tax_rate = Decimal("0.00")
            self.tax_name = self.tax_name or None
        if self.qty is None or self.qty <= 0:
            raise ValidationError({"qty": "Quantity must be > 0."})
        if self.exchange_rate is None or self.exchange_rate <= 0:
            raise ValidationError({"exchange_rate": "Exchange rate must be > 0."})

    def recompute(self):
        qty = self.qty or Decimal("0.00")
        rate = self.unit_price_charge or Decimal("0.00")
        tax_rate = (self.tax_rate or Decimal("0.00")) / Decimal("100.00")
        self.subtotal_charge = (rate * qty)
        self.tax_amount_charge = (self.subtotal_charge * tax_rate)
        self.total_with_tax_charge = (self.subtotal_charge + self.tax_amount_charge)
        ex = self.exchange_rate or Decimal("1.000000")
        self.unit_price_invoice = (rate * ex)
        self.subtotal_invoice = (self.subtotal_charge * ex)
        self.tax_amount_invoice = (self.tax_amount_charge * ex)
        self.total_with_tax_invoice = (self.total_with_tax_charge * ex)

    def save(self, *args, **kwargs):
        self.full_clean()
        self.recompute()
        return super().save(*args, **kwargs)


class QuotationChargeLine(QuotationLineBase):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="charge_lines")

    class Meta:
        ordering = ["-id"]
        verbose_name = "Quotation Charge"
        verbose_name_plural = "Quotation Charges"


class QuotationCostLine(QuotationLineBase):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="cost_lines")

    class Meta:
        ordering = ["-id"]
        verbose_name = "Quotation Costing"
        verbose_name_plural = "Quotation Costings"
