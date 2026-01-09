import uuid
from decimal import Decimal
from django.db import models
from actors.models import Vendor
from actors.models import Customer
from master.models import UnitofMeasurement, UnitofMeasurementLength
from core.utils.coreModels import BranchScopedStampedOwnedActive


PICKUP_REQUEST_STATUS = (
    ("DRAFT","Draft"), ("PENDING","Pending / Awaiting Confirmation"), ("CONFIRMED","Confirmed / Scheduled"),
    ("ASSIGNED","Assigned"), ("IN_TRANSIT","In Transit / On the Way"), ("ARRIVED","Arrived at Location"),
    ("PICKED_UP","Picked Up"), ("FAILED","Failed / Attempted"), ("CANCELLED","Cancelled"),
    ("COMPLETED","Completed / Closed"), ("RESCHEDULED","Rescheduled"), ("ON_HOLD","On Hold"),
    ("PARTIALLY_PICKED","Partially Picked"),
)

DELIVERY_STATUS = (("PENDING","Pending"), ("OUT_FOR_DELIVERY","Out for delivery"), ("DELIVERED","Delivered"), ("FAILED","Failed"), ("CANCELLED","Cancelled"))


class Vehicle(BranchScopedStampedOwnedActive):
    number_plate = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=50)
    brand = models.CharField(max_length=50, blank=True, null=True)
    model = models.CharField(max_length=50, blank=True, null=True)
    capacity = models.PositiveIntegerField(blank=True, null=True, help_text="Load capacity in kg")
    remarks = models.TextField(blank=True, null=True)
    class Meta: verbose_name="Vehicle"; verbose_name_plural="Vehicles"; indexes=[models.Index(fields=["number_plate"]), models.Index(fields=["branch"]), models.Index(fields=["active"])]
    def __str__(self): return f"{self.number_plate} ({self.vehicle_type})"


class Rider(BranchScopedStampedOwnedActive):
    class Gender(models.TextChoices): MALE="male","Male"; FEMALE="female","Female"; OTHER="other","Other"
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    class Meta: verbose_name="Rider"; verbose_name_plural="Riders"; indexes=[models.Index(fields=["full_name"]), models.Index(fields=["phone"]), models.Index(fields=["branch"]), models.Index(fields=["active"])]
    def __str__(self): return f"{self.full_name} - {self.phone}"


class PickupRequest(BranchScopedStampedOwnedActive):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    Customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="pickup_requests")
    location = models.CharField(max_length=255)
    requested_date = models.DateField()
    time_window = models.CharField(max_length=100, help_text="e.g., 9AM - 11AM")
    expected_packages = models.PositiveIntegerField()
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=PICKUP_REQUEST_STATUS, default="PENDING")
    class Meta: verbose_name="Pickup Request"; verbose_name_plural="Pickup Requests"; ordering=["-created"]; indexes=[models.Index(fields=["status"]), models.Index(fields=["requested_date"]), models.Index(fields=["Customer"]), models.Index(fields=["branch"]), models.Index(fields=["active"])]
    def __str__(self): return f"PickupRequest {self.code} - {self.Customer}"


class PickupOrder(BranchScopedStampedOwnedActive):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    pickup_request = models.ForeignKey(PickupRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="pickup_orders")
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="pickup_orders")
    from_location = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    sender_Customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="sent_pickups")
    sender_address = models.CharField(max_length=255)
    sender_phone = models.CharField(max_length=20)
    sender_alt_number = models.CharField(max_length=20, blank=True, null=True)
    receiver_name = models.CharField(max_length=100)
    receiver_address = models.CharField(max_length=255)
    receiver_phone = models.CharField(max_length=20)
    receiver_alt_no = models.CharField(max_length=20, blank=True, null=True)
    service_type = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=50)
    total_charge = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    piece = models.PositiveIntegerField(default=1)
    cod = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    ref_no = models.CharField(max_length=100, blank=True, null=True)
    instruction = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=PICKUP_REQUEST_STATUS, default="PENDING")
    class Meta: verbose_name="Pickup Order"; verbose_name_plural="Pickup Orders"; ordering=["-created"]; indexes=[models.Index(fields=["status"]), models.Index(fields=["vendor"]), models.Index(fields=["sender_Customer"]), models.Index(fields=["branch"]), models.Index(fields=["active"])]
    def __str__(self): return f"PickupOrder {self.code} - {self.sender_Customer} → {self.receiver_name}"


class PickupPackage(BranchScopedStampedOwnedActive):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    pickup_order = models.ForeignKey(PickupOrder, on_delete=models.CASCADE, related_name="pickup_packages")
    goods_description = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    fragile = models.BooleanField(default=False)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    weight_unit = models.ForeignKey(UnitofMeasurement, on_delete=models.PROTECT)
    length = models.DecimalField(max_digits=10, decimal_places=2)
    bredth = models.DecimalField(max_digits=10, decimal_places=2)  # keeping your original field name
    width = models.DecimalField(max_digits=10, decimal_places=2)
    length_unit = models.ForeignKey(UnitofMeasurementLength, on_delete=models.PROTECT)
    class Meta: verbose_name="Pickup Package"; verbose_name_plural="Pickup Packages"; ordering=["-created"]; indexes=[models.Index(fields=["pickup_order"]), models.Index(fields=["branch"]), models.Index(fields=["active"])]
    def __str__(self): return f"Pkg {self.code} for {self.pickup_order_id} ({self.weight} {self.weight_unit})"


class PickupRunsheet(BranchScopedStampedOwnedActive):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, blank=True, null=True)
    rider = models.ForeignKey(Rider, on_delete=models.PROTECT, blank=True, null=True)
    pickup_orders = models.ManyToManyField(PickupOrder, related_name="pickup_runsheets", blank=True)
    status = models.CharField(max_length=50, choices=PICKUP_REQUEST_STATUS, default="DRAFT")  # FIXED: valid default
    class Meta: verbose_name="Pickup Runsheet"; verbose_name_plural="Pickup Runsheets"; ordering=["-created"]; indexes=[models.Index(fields=["status"]), models.Index(fields=["branch"]), models.Index(fields=["active"])]
    def __str__(self): return f"PickupRunsheet {self.code} - Rider: {self.rider.full_name if self.rider else 'N/A'}"


class DeliveryOrder(BranchScopedStampedOwnedActive):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    pickup_order = models.ForeignKey(PickupOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="delivery_orders")
    delivery_address = models.CharField(max_length=255)
    delivery_status = models.CharField(max_length=50, choices=DELIVERY_STATUS, default="PENDING")
    delivery_date = models.DateField(blank=True, null=True)
    delivered_by = models.ForeignKey(Rider, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    class Meta: verbose_name="Delivery Order"; verbose_name_plural="Delivery Orders"; ordering=["-created"]; indexes=[models.Index(fields=["delivery_status"]), models.Index(fields=["delivery_date"]), models.Index(fields=["branch"]), models.Index(fields=["active"])]
    def __str__(self): return f"Delivery {self.code} - {self.delivery_status}"


class DeliveryAttempt(BranchScopedStampedOwnedActive):
    delivery_order = models.ForeignKey(DeliveryOrder, on_delete=models.CASCADE, related_name="attempts")
    attempt_number = models.PositiveIntegerField()
    status = models.CharField(max_length=50, default="ATTEMPTED")
    remarks = models.TextField(blank=True, null=True)
    attempt_date = models.DateTimeField(auto_now_add=True)
    class Meta: verbose_name="Delivery Attempt"; verbose_name_plural="Delivery Attempts"; ordering=["-attempt_date"]; indexes=[models.Index(fields=["delivery_order"]), models.Index(fields=["attempt_number"])]
    def __str__(self): return f"Attempt #{self.attempt_number} - Delivery {self.delivery_order_id}"


class ProofOfDelivery(BranchScopedStampedOwnedActive):
    delivery_order = models.OneToOneField(DeliveryOrder, on_delete=models.CASCADE, related_name="pod")
    recipient_name = models.CharField(max_length=100)
    signature = models.ImageField(upload_to="signatures/", blank=True, null=True)
    photo = models.ImageField(upload_to="delivery_photos/", blank=True, null=True)
    delivery_time = models.DateTimeField(auto_now_add=True)
    class Meta: verbose_name="Proof of Delivery"; verbose_name_plural="Proofs of Delivery"
    def __str__(self): return f"POD for Delivery {self.delivery_order_id}"


class DeliveryRunsheet(BranchScopedStampedOwnedActive):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    rider = models.ForeignKey(Rider, on_delete=models.PROTECT)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    delivery_orders = models.ManyToManyField(DeliveryOrder, related_name="delivery_runsheets", blank=True)
    run_date = models.DateField()
    status = models.CharField(max_length=50, default="CREATED")
    remarks = models.TextField(blank=True, null=True)
    class Meta: verbose_name="Delivery Runsheet"; verbose_name_plural="Delivery Runsheets"; ordering=["-created"]; indexes=[models.Index(fields=["run_date"]), models.Index(fields=["branch"]), models.Index(fields=["active"])]
    def __str__(self): return f"DeliveryRunsheet {self.code} - Rider: {self.rider.full_name if self.rider else 'N/A'}"


class ReturnToVendor(BranchScopedStampedOwnedActive):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    reference_order = models.ForeignKey(PickupOrder, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=50, default="INITIATED")
    processed_date = models.DateField(blank=True, null=True)
    class Meta: verbose_name="Return To Vendor"; verbose_name_plural="Returns To Vendor"; ordering=["-created"]; indexes=[models.Index(fields=["vendor"]), models.Index(fields=["status"]), models.Index(fields=["branch"]), models.Index(fields=["active"])]
    def __str__(self): return f"RTV {self.code} - {self.vendor}"


class RtvBranchReturn(BranchScopedStampedOwnedActive):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    pickup_order = models.ForeignKey(PickupOrder, on_delete=models.CASCADE)
    from_branch = models.ForeignKey("master.Branch", on_delete=models.PROTECT, related_name="rtv_from")
    to_branch = models.ForeignKey("master.Branch", on_delete=models.PROTECT, related_name="rtv_to")
    reason = models.TextField()
    status = models.CharField(max_length=50, default="PENDING")
    class Meta: verbose_name="RTV Branch Return"; verbose_name_plural="RTV Branch Returns"; ordering=["-created"]; indexes=[models.Index(fields=["status"]), models.Index(fields=["from_branch"]), models.Index(fields=["to_branch"]), models.Index(fields=["branch"]), models.Index(fields=["active"])]
    def __str__(self): return f"RTVBranchReturn {self.code} ({self.from_branch} → {self.to_branch})"


class DispatchManifest(BranchScopedStampedOwnedActive):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    rider = models.ForeignKey(Rider, on_delete=models.PROTECT)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    orders = models.ManyToManyField(PickupOrder, related_name="dispatch_manifests", blank=True)
    dispatch_date = models.DateField()
    status = models.CharField(max_length=50, default="DISPATCHED")
    class Meta: verbose_name="Dispatch Manifest"; verbose_name_plural="Dispatch Manifests"; ordering=["-created"]; indexes=[models.Index(fields=["dispatch_date"]), models.Index(fields=["status"]), models.Index(fields=["branch"]), models.Index(fields=["active"])]
    def __str__(self): return f"DispatchManifest {self.code}"


class ReceiveManifest(BranchScopedStampedOwnedActive):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    from_branch = models.ForeignKey("master.Branch", on_delete=models.PROTECT, related_name="receive_from_branch")
    to_branch = models.ForeignKey("master.Branch", on_delete=models.PROTECT, related_name="receive_to_branch")
    orders = models.ManyToManyField(PickupOrder, related_name="receive_manifests", blank=True)
    receive_date = models.DateField()
    status = models.CharField(max_length=50, default="RECEIVED")
    class Meta: verbose_name="Receive Manifest"; verbose_name_plural="Receive Manifests"; ordering=["-created"]; indexes=[models.Index(fields=["receive_date"]), models.Index(fields=["status"]), models.Index(fields=["from_branch"]), models.Index(fields=["to_branch"]), models.Index(fields=["branch"]), models.Index(fields=["active"])]
    def __str__(self): return f"ReceiveManifest {self.code}"
