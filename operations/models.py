# operations/models.py
from __future__ import annotations

from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from master.models import UnitofMeasurementLength, UnitofMeasurement
from core.utils.coreModels import BranchScopedStampedOwnedActive


PAYMENT_CHOICES = [
    ("prepaid", "Prepaid"),
    ("collect", "Collect"),
    ("third_party_billing", "Third Party Billing"),
    ("freight_prepaid_and_add", "Freight Prepaid and Add"),
    ("cod", "Cash on Delivery"),
    ("credit_account", "Credit Account"),
    ("eft", "Electronic Funds Transfer"),
]


def generate_custom_si():
    last_shipment = Shipment.objects.all().order_by("-id").first()
    last_shipment_id = last_shipment.id if last_shipment else 0
    unique_number = last_shipment_id + 500
    return f"SI-{unique_number:08d}"


def generate_custom_package_np():
    last_pkg = ShipmentPackages.objects.all().order_by("-id").first()
    last_pkg_id = last_pkg.id if last_pkg else 0
    unique_number = last_pkg_id + 5500
    return f"PKG-{unique_number:08d}"


class Shipment(BranchScopedStampedOwnedActive):
    class ShipmentMainType(models.TextChoices):
        BOOKING = "Booking", "Booking"
        DIRECT = "Direct", "Direct"
        MASTER = "Master", "Master"

    class TransportationMode(models.TextChoices):
        AIR = "air", "Air"
        OCEAN = "ocean", "Ocean"
        LAND = "land", "Land"

    class Direction(models.TextChoices):
        EXPORT = "export", "Export"
        IMPORT = "import", "Import"

    class ServiceType(models.TextChoices):
        FCL = "fcl", "FCL"
        LCL = "lcl", "LCL"

    class UnitType(models.TextChoices):
        SI_METRIC = "si_metric", "SI (Metric)"
        IMPERIAL = "imperial", "Imperial"

    class ShipmentType(models.TextChoices):
        FCL = "fcl", "FCL"
        LCL = "lcl", "LCL"
        AIR_CARGO = "air_cargo", "Air Cargo"
        ROAD = "road", "Road"

    class Incoterms(models.TextChoices):
        EXW = "EXW", "EXW"
        FOB = "FOB", "FOB"
        CIF = "CIF", "CIF"
        DAP = "DAP", "DAP"

    class PaymentTerm(models.TextChoices):
        NONE = "none", "None"
        CC = "cc", "CC"
        CP = "cp", "CP"
        PP = "pp", "PP"
        FOB = "fob", "FOB"

    shipment_main_type = models.CharField(
        max_length=20, choices=ShipmentMainType.choices, default=ShipmentMainType.BOOKING
    )
    transportation_mode = models.CharField(
        max_length=10, choices=TransportationMode.choices, default=TransportationMode.AIR
    )
    direction = models.CharField(max_length=10, choices=Direction.choices, default=Direction.EXPORT)
    service_type = models.CharField(max_length=10, choices=ServiceType.choices, blank=True, null=True)

    roro = models.BooleanField(default=False)
    third_party_booking = models.BooleanField(default=False)

    origin_agent = models.CharField(max_length=64, blank=True, null=True)
    destination_agent = models.CharField(max_length=64, blank=True, null=True)
    origin_agency = models.CharField(max_length=64, blank=True, null=True)
    destination_agency = models.CharField(max_length=64, blank=True, null=True)

    origin_port = models.CharField(max_length=16)
    destination_port = models.CharField(max_length=16)

    shipper = models.CharField(max_length=64, blank=True, null=True)
    consignee = models.CharField(max_length=64, blank=True, null=True)

    unit_type = models.CharField(max_length=20, choices=UnitType.choices, default=UnitType.SI_METRIC)

    created_date = models.DateField(blank=True, null=True)
    doc_ref_no = models.CharField(max_length=100, blank=True, null=True)

    received_currency = models.CharField(max_length=10, blank=True, null=True)
    received_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    scheduled_start_date = models.DateField(blank=True, null=True)
    scheduled_end_date = models.DateField(blank=True, null=True)

    shipment_type = models.CharField(max_length=20, choices=ShipmentType.choices, blank=True, null=True)
    incoterms = models.CharField(max_length=10, choices=Incoterms.choices, blank=True, null=True)
    payment_term = models.CharField(max_length=10, choices=PaymentTerm.choices, default=PaymentTerm.NONE)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.shipment_main_type} {self.origin_port}->{self.destination_port} ({self.id})"


class ShipmentDocument(BranchScopedStampedOwnedActive):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="documents")
    document = models.FileField(upload_to="shipment_documents/%Y/%m/")
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Doc {self.id} for {self.shipment_id}"


class ShipmentNote(BranchScopedStampedOwnedActive):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="notes")
    note = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Note {self.note} ({self.shipment_id})"


class ShipmentTransportInfo(BranchScopedStampedOwnedActive):
    class TransportMode(models.TextChoices):
        AIR = "AIR", "Air"
        OCEAN = "OCEAN", "Ocean"
        LAND = "LAND", "Land"

    class LegType(models.TextChoices):
        PRE = "PRE", "Pre-Transportation"
        MAIN = "MAIN", "Main Carriage"
        POST = "POST", "Post-Transportation"

    class TransportationType(models.TextChoices):
        DIRECT = "DIRECT", "Direct"
        CONSOL = "CONSOL", "Consolidation"
        TRANSSHIP = "TRANSSHIP", "Transshipment"

    shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE, related_name="transport_info")

    leg_type = models.CharField(max_length=10, choices=LegType.choices, default=LegType.MAIN)
    transport_mode = models.CharField(max_length=10, choices=TransportMode.choices, default=TransportMode.AIR)

    port_of_arrival = models.CharField(max_length=64, blank=True, null=True)
    port_of_departure = models.CharField(max_length=64, blank=True, null=True)
    port_of_delivery = models.CharField(max_length=64, blank=True, null=True)

    transportation_type = models.CharField(max_length=20, choices=TransportationType.choices, blank=True, null=True)
    booking_agency = models.CharField(max_length=64, blank=True, null=True)

    expected_start_date = models.DateField(blank=True, null=True)
    expected_end_date = models.DateField(blank=True, null=True)
    actual_start_date = models.DateField(blank=True, null=True)
    actual_end_date = models.DateField(blank=True, null=True)

    state = models.CharField(max_length=100, blank=True, null=True)

    airline = models.CharField(max_length=100, blank=True, null=True)
    flight_no = models.CharField(max_length=60, blank=True, null=True)
    terminal = models.CharField(max_length=60, blank=True, null=True)
    air_waybill_number = models.CharField(max_length=80, blank=True, null=True)
    mawb_date = models.DateField(blank=True, null=True)
    cut_off_date = models.DateField(blank=True, null=True)

    bill_of_lading = models.CharField(max_length=100, blank=True, null=True)
    voyage_no = models.CharField(max_length=100, blank=True, null=True)

    tracking_no = models.CharField(max_length=120, blank=True, null=True)
    ground_waybill_no = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.get_leg_type_display()} TransportInfo for {self.shipment_id}"


class ShipmentPackages(BranchScopedStampedOwnedActive):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="shipment_packages")
    shipment_package = models.CharField(max_length=50, verbose_name="Shipment Number", default=generate_custom_package_np)

    good_desc = models.CharField(max_length=50, null=True, blank=True, verbose_name="Good Desc")
    country_of_origin = models.CharField(max_length=50, null=True, blank=True, verbose_name="Country of Origin")
    fragile = models.BooleanField(default=False)
    hs_code = models.CharField(max_length=50, null=True, blank=True, verbose_name="HS Code")

    length = models.FloatField(verbose_name="Length")
    width = models.FloatField(verbose_name="Width")
    height = models.FloatField(verbose_name="Height")

    package_unit = models.ForeignKey(
        UnitofMeasurementLength, on_delete=models.PROTECT, verbose_name="Unit of Length", related_name="pkg_unit_length"
    )

    gross_weight = models.FloatField(verbose_name="Gross Weight", blank=True, null=True)
    mass_unit = models.ForeignKey(
        UnitofMeasurement, on_delete=models.PROTECT, verbose_name="Unit of Mass/Weight", related_name="pkg_unit_mass", blank=True, null=True
    )

    quantity = models.PositiveBigIntegerField(default=1, verbose_name="Quantity")
    volumetric_weight = models.FloatField(verbose_name="Volumetric Weight", blank=True, null=True, default=0)
    chargable = models.FloatField(blank=True, null=True, default=0)

    remarks = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Packages"
        verbose_name_plural = "Packages"

    def __str__(self):
        return str(self.good_desc)


class ShipmentManifest(models.Model):
    id = models.BigAutoField(primary_key=True, verbose_name="ID")
    master_shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE, related_name="house_shipment", verbose_name="Master Shipment")
    manifest_number = models.CharField(max_length=100, unique=True, default=generate_custom_si, verbose_name="Manifest Number")
    manifest_si_number = models.CharField(max_length=100, unique=True, default=generate_custom_si, verbose_name="Manifest SI Number")
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Shipment Manifest"
        verbose_name_plural = "Shipment Manifests"
        ordering = ["-created"]

    def __str__(self):
        return f"Manifest {self.manifest_number} (SI: {self.manifest_si_number})"


class ShipmentManifestBooking(models.Model):
    shipment_manifest = models.ForeignKey(ShipmentManifest, on_delete=models.CASCADE, related_name="manifest_bookings", verbose_name="Shipment Manifest")
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="manifest_shipments", verbose_name="Shipment")
    is_loaded = models.BooleanField(default=False, verbose_name="Is Loaded")
    loaded_count = models.PositiveIntegerField(default=0, blank=True, null=True, verbose_name="Loaded Count")
    is_manifested = models.BooleanField(default=False, verbose_name="Is Manifested")
    shipment_items_loaded = models.ManyToManyField("warehouse.HandlingUnit", related_name="loaded_items", blank=True, verbose_name="Shipment Items Loaded")
    house_shipment = models.ForeignKey("ShipmentManifestHouse", on_delete=models.CASCADE, related_name="manifest_bookings", null=True, blank=True, verbose_name="House Shipment")
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Shipment Manifest Booking"
        verbose_name_plural = "Shipment Manifest Bookings"

    def __str__(self):
        return f"Booking for {self.shipment} in {self.shipment_manifest}"


class ShipmentManifestHouse(models.Model):
    shipment_manifest = models.ForeignKey(ShipmentManifest, on_delete=models.CASCADE, related_name="houses", verbose_name="Shipment Manifest")
    active = models.BooleanField(default=True)
    shipment_manifest_booking = models.ManyToManyField("ShipmentManifestBooking", related_name="manifest_houses", blank=True, verbose_name="Shipment Manifest Bookings")

    house_np = models.CharField(max_length=100, verbose_name="House NP")
    waybill_no = models.CharField(max_length=100, verbose_name="Waybill Number")

    exporter_name = models.CharField(max_length=255, verbose_name="Exporter Name")
    forwader_name = models.CharField(max_length=255, verbose_name="Forwarder Name")
    exporter_address = models.TextField(verbose_name="Exporter Address")
    forwader_address = models.TextField(verbose_name="Forwarder Address")

    created = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Manifest House"
        verbose_name_plural = "Manifest Houses"
        ordering = ["-created"]

    def __str__(self):
        return f"{self.house_np} - {self.waybill_no}"


class PaymentSummary(BranchScopedStampedOwnedActive):
    shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE, related_name="payment_summary")

    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)     # sell total (from ShipmentCharges)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)      # received (from invoice allocations)
    total_costings = models.DecimalField(max_digits=12, decimal_places=2, default=0)   # buy total (from ShipmentCostings)
    paid_costings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, null=True, blank=True)
    payment_status = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default="prepaid")

    class Meta:
        verbose_name = "Payment Summary"
        verbose_name_plural = "Payment Summary"

    def __str__(self) -> str:
        return f"Payment Summary for {self.shipment}"

    def recompute_from_lines(self, save: bool = True) -> dict:
        sell = self.shipment_charges.filter(active=True).aggregate(s=models.Sum("total_with_tax_invoice")).get("s") or Decimal("0")
        buy = self.shipment_costings.filter(active=True).aggregate(s=models.Sum("total_with_tax_invoice")).get("s") or Decimal("0")

        self.total_amount = sell
        self.total_costings = buy
        self.profit_amount = (sell - buy)

        if save:
            type(self).objects.filter(pk=self.pk).update(
                total_amount=self.total_amount,
                total_costings=self.total_costings,
                profit_amount=self.profit_amount,
            )

        return {"total_amount": self.total_amount, "total_costings": self.total_costings, "profit_amount": self.profit_amount}


class ShipmentLineBase(BranchScopedStampedOwnedActive):
    """
    IMPORTANT CHANGE:
    - previously you had created/updated fields here and no `active`.
    - now it inherits BranchScopedStampedOwnedActive, so you get:
      branch, created, updated, user_add, active, is_system_generated.
    """

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

    charge_name = models.CharField(max_length=100)
    charge_type = models.CharField(max_length=50, default="Fixed")

    qty = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("1.00"))

    tax_name = models.CharField(max_length=100, blank=True, null=True)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    is_tax_exempt = models.BooleanField(default=False)

    remarks = models.TextField(blank=True, null=True)
    reference_no = models.CharField(max_length=100, blank=True, null=True)

    charge_currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    invoice_currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("1.000000"))

    unit_price_charge = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    subtotal_charge = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_amount_charge = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_with_tax_charge = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    unit_price_invoice = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    subtotal_invoice = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_amount_invoice = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_with_tax_invoice = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        abstract = True

    def clean(self):
        if self.is_tax_exempt:
            self.tax_rate = Decimal("0.00")
            self.tax_name = None

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


class ShipmentCharges(ShipmentLineBase):
    """
    SELL lines (what you bill customers).

    IMPORTANT ADDITIONS:
    - invoice (FK to sales.Sales)
    - sales_item (OneToOne to sales.SalesItem)
    - is_invoiced + invoiced_at
    """
    payment_summary = models.ForeignKey(PaymentSummary, on_delete=models.CASCADE, related_name="shipment_charges")

    invoice = models.ForeignKey("sales.Sales", on_delete=models.SET_NULL, null=True, blank=True, related_name="shipment_charges")
    sales_item = models.OneToOneField("sales.SalesItem", on_delete=models.SET_NULL, null=True, blank=True, related_name="from_shipment_charge")

    is_invoiced = models.BooleanField(default=False)
    invoiced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Charges"
        verbose_name_plural = "Charges"

    def mark_invoiced(self, invoice, sales_item):
        self.invoice = invoice
        self.sales_item = sales_item
        self.is_invoiced = True
        self.invoiced_at = timezone.now()
        self.save(update_fields=["invoice", "sales_item", "is_invoiced", "invoiced_at"])


class ShipmentCostings(ShipmentLineBase):
    """
    BUY lines (what you pay vendors).
    """
    payment_summary = models.ForeignKey(PaymentSummary, on_delete=models.CASCADE, related_name="shipment_costings")

    class Meta:
        verbose_name = "Costing"
        verbose_name_plural = "Costing"
