# admin.py (actors app) - NO autocomplete_fields + no updated_at readonly

from django.contrib import admin

from .models import (
    BookingAgency,
    Carrier,
    CustomsAgent,
    Vendor,
    Customer,
    CustomerPerson,
    CustomerCompany,
    Department,
    Designation,
    Employee,
    MainActor,
    Supplier,
)


# ---------------------------
# Common Actions
# ---------------------------
@admin.action(description="Mark selected as Active")
def make_active(modeladmin, request, queryset):
    queryset.update(active=True)


@admin.action(description="Mark selected as Inactive")
def make_inactive(modeladmin, request, queryset):
    queryset.update(active=False)


# ---------------------------
# Helper Mixin (safe defaults)
# ---------------------------
class BranchScopedAdminMixin(admin.ModelAdmin):
    """
    Assumes base model has: branch, active, created.
    (Your error shows updated_at does NOT exist.)
    """
    actions = (make_active, make_inactive)
    list_filter = ("branch", "active")
    ordering = ("-created",)
    readonly_fields = ("created",)


# ---------------------------
# BookingAgency
# ---------------------------
@admin.register(BookingAgency)
class BookingAgencyAdmin(BranchScopedAdminMixin):
    list_display = (
        "name",
        "transportation_mode",
        "cellphone_country_code",
        "cellphone",
        "country",
        "branch",
        "active",
    )
    list_filter = BranchScopedAdminMixin.list_filter + ("transportation_mode", "country")
    search_fields = (
        "name",
        "email",
        "telephone",
        "cellphone",
        "iata_code",
        "waybill_prefix",
        "trn",
        "tax_ref_no",
        "account_no",
    )


# ---------------------------
# Carrier
# ---------------------------
@admin.register(Carrier)
class CarrierAdmin(BranchScopedAdminMixin):
    list_display = (
        "name",
        "transportation_mode",
        "cellphone_country_code",
        "cellphone",
        "country",
        "branch",
        "active",
    )
    list_filter = BranchScopedAdminMixin.list_filter + ("transportation_mode", "country")
    search_fields = (
        "name",
        "email",
        "telephone",
        "cellphone",
        "trn",
        "tax_ref_no",
        "account_no",
    )


# ---------------------------
# CustomsAgent
# ---------------------------
@admin.register(CustomsAgent)
class CustomsAgentAdmin(BranchScopedAdminMixin):
    list_display = ("name", "mobile", "emirates_no", "country", "branch", "active")
    list_filter = BranchScopedAdminMixin.list_filter + ("country",)
    search_fields = ("name", "mobile", "emirates_no", "email", "trn", "tax_ref_no", "account_no")


# ---------------------------
# Vendor
# ---------------------------
@admin.register(Vendor)
class VendorAdmin(BranchScopedAdminMixin):
    list_display = ("name", "cellphone_country_code", "cellphone", "category", "country", "branch", "active")
    list_filter = BranchScopedAdminMixin.list_filter + ("country", "category")
    search_fields = ("name", "cellphone", "email", "trn", "tax_ref_no", "account_no")


# ---------------------------
# Customer Inlines
# ---------------------------
class CustomerPersonInline(admin.StackedInline):
    model = CustomerPerson
    extra = 0
    max_num = 1


class CustomerCompanyInline(admin.StackedInline):
    model = CustomerCompany
    extra = 0
    max_num = 1


@admin.register(Customer)
class CustomerAdmin(BranchScopedAdminMixin):
    list_display = (
        "id",
        "customer_type",
        "is_shipper",
        "is_consignee",
        "is_customer",
        "mobile_country_code",
        "mobile_no",
        "country",
        "branch",
        "active",
        "created",
    )
    list_filter = BranchScopedAdminMixin.list_filter + (
        "customer_type",
        "is_shipper",
        "is_consignee",
        "is_customer",
        "country",
    )
    search_fields = (
        "mobile_no",
        "telephone_no",
        "fax_no",
        "account_no",
        "tax_ref_no",
        "remarks",
        "person__first_name",
        "person__middle_name",
        "person__last_name",
        "company__company_name",
        "company__account_number",
    )
    inlines = (CustomerPersonInline, CustomerCompanyInline)

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


# ---------------------------
# Department
# ---------------------------
@admin.register(Department)
class DepartmentAdmin(BranchScopedAdminMixin):
    list_display = ("name", "branch", "active", "created")
    search_fields = ("name",)
    ordering = ("name",)


# ---------------------------
# Designation
# ---------------------------
@admin.register(Designation)
class DesignationAdmin(BranchScopedAdminMixin):
    list_display = ("name", "branch", "active", "created")
    search_fields = ("name",)
    ordering = ("name",)


# ---------------------------
# Employee
# ---------------------------
@admin.register(Employee)
class EmployeeAdmin(BranchScopedAdminMixin):
    list_display = (
        "full_name",
        "primary_email",
        "mobile_country_code",
        "mobile_no",
        "department",
        "branch",
        "active",
        "created",
    )
    list_filter = BranchScopedAdminMixin.list_filter + ("department", "is_resident", "gender")
    search_fields = (
        "first_name",
        "middle_name",
        "last_name",
        "primary_email",
        "secondary_email",
        "mobile_no",
        "business_phone",
        "present_city",
        "present_country",
        "permanent_city",
        "permanent_country",
    )

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


# ---------------------------
# MainActor
# ---------------------------
@admin.register(MainActor)
class MainActorAdmin(BranchScopedAdminMixin):
    list_display = ("display_name", "actor_type", "branch", "active", "created")
    list_filter = BranchScopedAdminMixin.list_filter + ("actor_type",)
    search_fields = ("display_name",)
    ordering = ("display_name", "-created")

    readonly_fields = ("display_name", "actor_type", "created")

    fieldsets = (
        ("Scope", {"fields": ("branch", "active")}),
        ("Type & Display", {"fields": ("actor_type", "display_name")}),
        (
            "Link exactly ONE",
            {
                "fields": (
                    "booking_agency",
                    "carrier",
                    "customs_agent",
                    "vendor",
                    "customer",
                    "department",
                    "designation",
                    "employee",
                )
            },
        ),
        ("Audit", {"fields": ("created",)}),
    )

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


# ---------------------------
# Supplier (currently pass)
# ---------------------------
@admin.register(Supplier)
class SupplierAdmin(BranchScopedAdminMixin):
    list_display = ("id", "branch", "active", "created")
    search_fields = ("id",)
