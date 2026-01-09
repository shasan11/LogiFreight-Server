from __future__ import annotations

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from core.utils.coreModels import BranchScopedStampedOwnedActive


class PartyBase(BranchScopedStampedOwnedActive):
    name = models.CharField(max_length=255)
    address = models.TextField()
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    agency = models.ForeignKey("master.MasterData", on_delete=models.PROTECT, related_name="%(class)s_agency")
    currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, related_name="%(class)s_currency")
    account = models.ForeignKey("accounting.AccountHead", on_delete=models.PROTECT, related_name="%(class)s_account")
    email = models.EmailField(blank=True, null=True)
    bank_info = models.TextField(blank=True, null=True)
    account_no = models.CharField(max_length=100, blank=True, null=True)
    trn = models.CharField(max_length=100, blank=True, null=True)
    tax_ref_no = models.CharField(max_length=100, blank=True, null=True)
    amount_limit = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    days_limit = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class BookingAgency(PartyBase):
    class TransportationMode(models.TextChoices):
        AIR = "air", "Air"
        OCEAN = "ocean", "Ocean"
        LAND = "land", "Land"

    transportation_mode = models.CharField(max_length=10, choices=TransportationMode.choices)
    telephone_country_code = models.CharField(max_length=10, blank=True, null=True)
    telephone = models.CharField(max_length=30, blank=True, null=True)
    extension = models.CharField(max_length=10, blank=True, null=True)
    cellphone_country_code = models.CharField(max_length=10)
    cellphone = models.CharField(max_length=30)
    iata_code = models.CharField(max_length=50, blank=True, null=True)
    waybill_prefix = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"]), models.Index(fields=["transportation_mode"]), models.Index(fields=["branch"])]
        constraints = [models.UniqueConstraint(fields=["branch", "name", "transportation_mode"], name="uniq_bookingagency_branch_name_mode")]


class Carrier(PartyBase):
    class TransportationMode(models.TextChoices):
        AIR = "air", "Air"
        OCEAN = "ocean", "Ocean"
        LAND = "land", "Land"

    transportation_mode = models.CharField(max_length=10, choices=TransportationMode.choices)
    telephone_country_code = models.CharField(max_length=10, blank=True, null=True)
    telephone = models.CharField(max_length=30, blank=True, null=True)
    extension = models.CharField(max_length=10, blank=True, null=True)
    cellphone_country_code = models.CharField(max_length=10)
    cellphone = models.CharField(max_length=30)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"]), models.Index(fields=["transportation_mode"]), models.Index(fields=["branch"])]
        constraints = [models.UniqueConstraint(fields=["branch", "name", "transportation_mode"], name="uniq_carrier_branch_name_mode")]

    def __str__(self):
        return f"{self.name} ({self.get_transportation_mode_display()})"


class CustomsAgent(PartyBase):
    emirates_no = models.CharField(max_length=50, blank=True, null=True)
    mobile = models.CharField(max_length=30)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"]), models.Index(fields=["mobile"]), models.Index(fields=["branch"])]
        constraints = [models.UniqueConstraint(fields=["branch", "name"], name="uniq_customsagent_branch_name")]


class Vendor(PartyBase):
    category = models.ForeignKey("master.MasterData", on_delete=models.PROTECT, related_name="vendor_categories", blank=True, null=True)
    cellphone_country_code = models.CharField(max_length=10)
    cellphone = models.CharField(max_length=30)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"]), models.Index(fields=["trn"]), models.Index(fields=["account_no"]), models.Index(fields=["branch"])]
        constraints = [models.UniqueConstraint(fields=["branch", "name"], name="uniq_vendor_branch_name")]


class Customer(BranchScopedStampedOwnedActive):
    class CustomerType(models.TextChoices):
        PERSON = "person", "Person"
        COMPANY = "company", "Company"

    customer_type = models.CharField(max_length=10, choices=CustomerType.choices)
    is_shipper = models.BooleanField(default=False)
    is_consignee = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=True)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    address_line_1 = models.TextField()
    address_line_2 = models.TextField(blank=True, null=True)
    telephone_country_code = models.CharField(max_length=10, blank=True, null=True)
    telephone_no = models.CharField(max_length=30, blank=True, null=True)
    extension = models.CharField(max_length=10, blank=True, null=True)
    mobile_country_code = models.CharField(max_length=10)
    mobile_no = models.CharField(max_length=30)
    fax_country_code = models.CharField(max_length=10, blank=True, null=True)
    fax_no = models.CharField(max_length=30, blank=True, null=True)
    salesman = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, blank=True, null=True, related_name="customers_salesman")
    account = models.ForeignKey("accounting.AccountHead", on_delete=models.PROTECT, related_name="customers")
    account_no = models.CharField(max_length=100, blank=True, null=True)
    tax_ref_no = models.CharField(max_length=100, blank=True, null=True)
    created_for = models.ForeignKey("master.Branch", on_delete=models.PROTECT, blank=True, null=True, related_name="customers_created_for")
    currency = models.ForeignKey("accounting.Currency", on_delete=models.PROTECT, related_name="customers_currency")
    credit_limit = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    days_limit = models.PositiveIntegerField(default=0)
    bank_info = models.TextField(blank=True, null=True)
    job_title = models.CharField(max_length=120, blank=True, null=True)
    department = models.CharField(max_length=120, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created"]
        indexes = [models.Index(fields=["customer_type"]), models.Index(fields=["mobile_no"]), models.Index(fields=["branch"])]

    def __str__(self):
        if self.customer_type == self.CustomerType.PERSON and hasattr(self, "person"):
            return self.person.full_name
        if self.customer_type == self.CustomerType.COMPANY and hasattr(self, "company"):
            return self.company.company_name
        return f"Customer ({self.id})"

    def clean(self):
        super().clean()
        if self.pk:
            has_person = hasattr(self, "person")
            has_company = hasattr(self, "company")
            if self.customer_type == self.CustomerType.PERSON and not has_person:
                raise ValidationError("Customer type PERSON requires CustomerPerson.")
            if self.customer_type == self.CustomerType.COMPANY and not has_company:
                raise ValidationError("Customer type COMPANY requires CustomerCompany.")


class CustomerPerson(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="person")
    prefix = models.CharField(max_length=20, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=100, blank=True, null=True)
    nationality = models.CharField(max_length=80, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    @property
    def full_name(self):
        return " ".join([p for p in [self.first_name, self.middle_name, self.last_name] if p])

    def __str__(self):
        return self.full_name


class CustomerCompany(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="company")
    company_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    account_number = models.CharField(max_length=100, blank=True, null=True)
    send_code_sms = models.BooleanField(default=False)
    send_code_email = models.BooleanField(default=False)
    contact_prefix = models.CharField(max_length=20, blank=True, null=True)
    contact_gender = models.CharField(max_length=10, choices=Gender.choices, blank=True, null=True)
    contact_first_name = models.CharField(max_length=100, blank=True, null=True)
    contact_middle_name = models.CharField(max_length=100, blank=True, null=True)
    contact_last_name = models.CharField(max_length=100, blank=True, null=True)
    contact_short_name = models.CharField(max_length=100, blank=True, null=True)
    contact_nationality = models.CharField(max_length=80, blank=True, null=True)

    def __str__(self):
        return self.company_name


class Department(BranchScopedStampedOwnedActive):
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"]), models.Index(fields=["branch"])]
        constraints = [models.UniqueConstraint(fields=["branch", "name"], name="uniq_department_branch_name")]

    def __str__(self):
        return self.name


class Designation(BranchScopedStampedOwnedActive):
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"]), models.Index(fields=["branch"])]
        constraints = [models.UniqueConstraint(fields=["branch", "name"], name="uniq_designation_branch_name")]

    def __str__(self):
        return self.name


class Employee(BranchScopedStampedOwnedActive):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    prefix = models.CharField(max_length=20, blank=True, null=True)
    first_name = models.CharField(max_length=120)
    middle_name = models.CharField(max_length=120, blank=True, null=True)
    last_name = models.CharField(max_length=120)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True, null=True)
    join_date = models.DateField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    primary_email = models.EmailField()
    secondary_email = models.EmailField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="employees")
    account = models.ForeignKey("accounting.AccountHead", on_delete=models.PROTECT, related_name="employees")
    nationality = models.CharField(max_length=80, blank=True, null=True)
    is_resident = models.BooleanField(default=False)
    mobile_country_code = models.CharField(max_length=10)
    mobile_no = models.CharField(max_length=30)
    fax_country_code = models.CharField(max_length=10, blank=True, null=True)
    fax_no = models.CharField(max_length=30, blank=True, null=True)
    residence_country_code = models.CharField(max_length=10, blank=True, null=True)
    residence_no = models.CharField(max_length=30, blank=True, null=True)
    business_country_code = models.CharField(max_length=10, blank=True, null=True)
    business_phone = models.CharField(max_length=30, blank=True, null=True)
    present_address = models.TextField()
    present_city = models.CharField(max_length=100, blank=True, null=True)
    present_zip_code = models.CharField(max_length=20, blank=True, null=True)
    present_country = models.CharField(max_length=100)
    present_state = models.CharField(max_length=100, blank=True, null=True)
    permanent_same_as_present = models.BooleanField(default=False)
    permanent_address = models.TextField()
    permanent_city = models.CharField(max_length=100, blank=True, null=True)
    permanent_zip_code = models.CharField(max_length=20, blank=True, null=True)
    permanent_country = models.CharField(max_length=100)
    permanent_state = models.CharField(max_length=100, blank=True, null=True)
    parent_employee = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="child_employees")
    designations = models.ManyToManyField(Designation, blank=True, related_name="employees")

    class Meta:
        ordering = ["first_name", "last_name"]
        indexes = [models.Index(fields=["first_name", "last_name"]), models.Index(fields=["mobile_no"]), models.Index(fields=["primary_email"]), models.Index(fields=["branch"])]
        constraints = [models.UniqueConstraint(fields=["branch", "primary_email"], name="uniq_employee_branch_primary_email")]

    @property
    def full_name(self):
        return " ".join([p for p in [self.first_name, self.middle_name, self.last_name] if p])

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if self.permanent_same_as_present:
            self.permanent_address = self.present_address
            self.permanent_city = self.present_city
            self.permanent_zip_code = self.present_zip_code
            self.permanent_country = self.present_country
            self.permanent_state = self.present_state
        super().save(*args, **kwargs)


class MainActor(BranchScopedStampedOwnedActive):
    class ActorType(models.TextChoices):
        BOOKING_AGENCY = "booking_agency", "Booking Agency"
        CARRIER = "carrier", "Carrier"
        CUSTOMS_AGENT = "customs_agent", "Customs Agent"
        VENDOR = "vendor", "Vendor"
        CUSTOMER = "customer", "Customer"
        DEPARTMENT = "department", "Department"
        DESIGNATION = "designation", "Designation"
        EMPLOYEE = "employee", "Employee"

    actor_type = models.CharField(max_length=30, choices=ActorType.choices, db_index=True)
    display_name = models.CharField(max_length=255, db_index=True, blank=True, null=True)

    booking_agency = models.OneToOneField("actors.BookingAgency", on_delete=models.CASCADE, related_name="main_actor", blank=True, null=True)
    carrier = models.OneToOneField("actors.Carrier", on_delete=models.CASCADE, related_name="main_actor", blank=True, null=True)
    customs_agent = models.OneToOneField("actors.CustomsAgent", on_delete=models.CASCADE, related_name="main_actor", blank=True, null=True)
    vendor = models.OneToOneField("actors.Vendor", on_delete=models.CASCADE, related_name="main_actor", blank=True, null=True)
    customer = models.OneToOneField("actors.Customer", on_delete=models.CASCADE, related_name="main_actor", blank=True, null=True)
    department = models.OneToOneField("actors.Department", on_delete=models.CASCADE, related_name="main_actor", blank=True, null=True)
    designation = models.OneToOneField("actors.Designation", on_delete=models.CASCADE, related_name="main_actor", blank=True, null=True)
    employee = models.OneToOneField("actors.Employee", on_delete=models.CASCADE, related_name="main_actor", blank=True, null=True)

    class Meta:
        ordering = ["display_name", "created"]
        indexes = [models.Index(fields=["branch", "actor_type"]), models.Index(fields=["branch", "display_name"])]

    def linked_object(self):
        for obj in [self.booking_agency, self.carrier, self.customs_agent, self.vendor, self.customer, self.department, self.designation, self.employee]:
            if obj:
                return obj
        return None

    def clean(self):
        super().clean()
        links = [self.booking_agency_id, self.carrier_id, self.customs_agent_id, self.vendor_id, self.customer_id, self.department_id, self.designation_id, self.employee_id]
        if sum(1 for x in links if x) != 1:
            raise ValidationError("MainActor must link to exactly one actor record.")
        obj = self.linked_object()
        if obj and getattr(obj, "branch_id", None) and self.branch_id and obj.branch_id != self.branch_id:
            raise ValidationError("MainActor.branch must match linked object's branch.")

    def save(self, *args, **kwargs):
        obj = self.linked_object()
        if obj:
            self.display_name = str(obj)
            if self.booking_agency_id:
                self.actor_type = self.ActorType.BOOKING_AGENCY
            elif self.carrier_id:
                self.actor_type = self.ActorType.CARRIER
            elif self.customs_agent_id:
                self.actor_type = self.ActorType.CUSTOMS_AGENT
            elif self.vendor_id:
                self.actor_type = self.ActorType.VENDOR
            elif self.customer_id:
                self.actor_type = self.ActorType.CUSTOMER
            elif self.department_id:
                self.actor_type = self.ActorType.DEPARTMENT
            elif self.designation_id:
                self.actor_type = self.ActorType.DESIGNATION
            elif self.employee_id:
                self.actor_type = self.ActorType.EMPLOYEE
        super().save(*args, **kwargs)

class Supplier(BranchScopedStampedOwnedActive):
    pass