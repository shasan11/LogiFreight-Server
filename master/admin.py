# admin.py
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    UnitofMeasurement,
    UnitofMeasurementLength,
    Ports,
    Branch,
    MasterData,
    ApplicationSettings,
    ShipmentPrefixes,
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
# Units (Mass)
# ---------------------------
@admin.register(UnitofMeasurement)
class UnitofMeasurementAdmin(SimpleHistoryAdmin):
    list_display = ("name", "symbol", "conversion_to_kg", "active", "created", "updated_at")
    list_filter = ("active", "created", "updated_at")
    search_fields = ("name", "symbol")
    ordering = ("name",)
    actions = (make_active, make_inactive)

    readonly_fields = ("id", "created", "updated_at")

    fieldsets = (
        ("Basic Info", {"fields": ("name", "symbol", "conversion_to_kg", "active")}),
        ("Audit", {"fields": ("add_by", "created", "updated_at", "id")}),
    )


# ---------------------------
# Units (Length)
# ---------------------------
@admin.register(UnitofMeasurementLength)
class UnitofMeasurementLengthAdmin(SimpleHistoryAdmin):
    list_display = ("name", "symbol", "conversion_to_cm", "active", "created", "updated_at")
    list_filter = ("active", "created", "updated_at")
    search_fields = ("name", "symbol")
    ordering = ("name",)
    actions = (make_active, make_inactive)

    readonly_fields = ("id", "created", "updated_at")

    fieldsets = (
        ("Basic Info", {"fields": ("name", "symbol", "conversion_to_cm", "active")}),
        ("Audit", {"fields": ("added_by", "created", "updated_at", "id")}),
    )


# ---------------------------
# Branch
# ---------------------------
@admin.register(Branch)
class BranchAdmin(SimpleHistoryAdmin):
    list_display = (
        "branch_id",
        "name",
        "city",
        "country",
        "status",
        "is_main_branch",
        "active",
        "created",
    )
    list_filter = ("status", "is_main_branch", "active", "country", "city", "created")
    search_fields = ("branch_id", "name", "city", "state", "country", "contact_number")
    ordering = ("name",)
    actions = (make_active, make_inactive)

    readonly_fields = ("id", "created", "updated_at")

    fieldsets = (
        ("Branch Identity", {"fields": ("branch_id", "name", "status", "is_main_branch", "active")}),
        ("Location", {"fields": ("address", "city", "state", "country")}),
        ("Contact", {"fields": ("contact_number", "established_date")}),
        ("Audit", {"fields": ("added_by", "created", "updated_at", "id")}),
    )


# ---------------------------
# Ports
# ---------------------------
@admin.register(Ports)
class PortsAdmin(SimpleHistoryAdmin):
    list_display = (
        "name",
        "symbol",
        "iso",
        "iata",
        "edi",
        "country",
        "city",
        "nearest_branch",
        "is_land",
        "is_air",
        "is_sea",
        "active",
    )
    list_filter = (
        "active",
        "country",
        "region",
        "city",
        "is_land",
        "is_air",
        "is_sea",
        "nearest_branch",
    )
    search_fields = ("name", "symbol", "iso", "iata", "edi", "country", "city", "region")
    ordering = ("name",)
    actions = (make_active, make_inactive)

    readonly_fields = ("id", "created", "updated_at")

    fieldsets = (
        ("Port Info", {"fields": ("name", "symbol", "active")}),
        ("Codes", {"fields": ("iso", "iata", "edi")}),
        ("Location", {"fields": ("country", "region", "city", "nearest_branch")}),
        ("Mode Support", {"fields": ("is_land", "is_air", "is_sea")}),
        ("Audit", {"fields": ("added_by", "created", "updated_at", "id")}),
    )


# ---------------------------
# Master Data
# ---------------------------
@admin.register(MasterData)
class MasterDataAdmin(SimpleHistoryAdmin):
    list_display = ("type_master", "name", "active")
    list_filter = ("type_master", "active")
    search_fields = ("type_master", "name", "description")
    ordering = ("type_master", "name")
    actions = (make_active, make_inactive)

    readonly_fields = ("id",)

    fieldsets = (
        ("Master Entry", {"fields": ("type_master", "name", "description", "active")}),
        ("System", {"fields": ("id",)}),
    )


# ---------------------------
# Singleton Admin Base
# ---------------------------
class SingletonAdmin(SimpleHistoryAdmin):
    """
    Prevent creating more than one instance from admin UI.
    Your model.save() already enforces it; this just makes admin UX clean.
    """

    def has_add_permission(self, request):
        # Only allow add if no rows exist
        model = self.model
        return not model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Usually you do NOT want singleton deletable from admin
        return False


# ---------------------------
# Singleton: Application Settings
# ---------------------------
@admin.register(ApplicationSettings)
class ApplicationSettingsAdmin(SingletonAdmin):
    list_display = ("name", "country", "state", "phone", "email", "PAN")
    search_fields = ("name", "country", "state", "phone", "email", "PAN")
    readonly_fields = ("id",)

    fieldsets = (
        ("Branding", {"fields": ("name", "logo", "favicon")}),
        ("Contact", {"fields": ("phone", "email", "address")}),
        ("Location", {"fields": ("country", "state")}),
        ("Tax", {"fields": ("PAN",)}),
        ("System", {"fields": ("id",)}),
    )


# ---------------------------
# Singleton: Shipment Prefixes
# ---------------------------
@admin.register(ShipmentPrefixes)
class ShipmentPrefixesAdmin(SingletonAdmin):
    list_display = (
        "shipment_prefix",
        "journal_voucher_prefix",
        "cash_transfer_prefix",
        "sales_prefix",
        "invoice_bundle_prefix",
        "vendor_bill_prefix",
        "booking_prefix",
        "order_number_prefix",
    )
    search_fields = (
        "shipment_prefix",
        "journal_voucher_prefix",
        "cash_transfer_prefix",
        "payment_request_prefix",
        "cheque_register_prefix",
        "sales_prefix",
        "invoice_bundle_prefix",
        "batch_invoice_prefix",
        "customer_payment_prefix",
        "sales_return_prefix",
        "expense_category_prefix",
        "supplier_prefix",
        "office_expense_prefix",
        "expense_payment_prefix",
        "vendor_bill_prefix",
        "bill_bundle_prefix",
        "master_job_prefix",
        "booking_prefix",
        "direct_order_prefix",
        "order_number_prefix",
        "vendor_payment_prefix",
        "payment_return_prefix",
    )
    readonly_fields = ("id",)

    fieldsets = (
        ("Logistics / Shipment", {"fields": ("shipment_prefix", "master_job_prefix", "booking_prefix", "direct_order_prefix", "order_number_prefix")}),
        ("Accounting", {"fields": ("journal_voucher_prefix", "cash_transfer_prefix", "cheque_register_prefix")}),
        ("Sales", {"fields": ("sales_prefix", "invoice_bundle_prefix", "batch_invoice_prefix", "customer_payment_prefix", "sales_return_prefix")}),
        ("Purchasing / Vendor", {"fields": ("supplier_prefix", "vendor_bill_prefix", "bill_bundle_prefix", "vendor_payment_prefix")}),
        ("Expenses", {"fields": ("expense_category_prefix", "office_expense_prefix", "expense_payment_prefix")}),
        ("Payments", {"fields": ("payment_request_prefix", "payment_return_prefix")}),
        ("System", {"fields": ("id",)}),
    )
