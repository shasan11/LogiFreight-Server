# from unfold import admin as uadmin
# from django.contrib import admin
# from .models import (
#     Vehicle,
#     Rider,
#     PickupRequest,
#     PickupOrder,
#     PickupPackages,
#     PickupRunsheet,
#     DeliveryOrder,
#     DeliveryAttempt,
#     ProofOfDelivery,
#     DeliveryRunsheet,
#     ReturnToVendor,
#     RtvBranchReturn,
#     DispatchManifest,
#     ReceiveManifest,
# )
# from .forms import (
#     VehicleForm,
#     RiderForm,
#     PickupRequestForm,
#     PickupOrderForm,
#     PickupPackagesForm,
#     PickupRunsheetForm,
#     DeliveryOrderForm,
#     DeliveryAttemptForm,
#     ProofOfDeliveryForm,
#     DeliveryRunsheetForm,
#     ReturnToVendorForm,
#     RtvBranchReturnForm,
#     DispatchManifestForm,
#     ReceiveManifestForm,
# )


# # -----------------
# # Inlines
# # -----------------
# class PickupPackagesInline(uadmin.StackedInline):
#     model = PickupPackages
#     form = PickupPackagesForm
#     extra = 0
     
#     fieldsets = (
#         ("Package", {
#             "fields": ("pickup_order",('goods_description','fragile','quantity'),( "weight", "weight_unit",), ("length", "bredth", "width", "length_unit"),),
#         }),
         
#     )



# class PickupOrderInline(uadmin.TabularInline):
#     model = PickupOrder
#     form = PickupOrderForm
#     extra = 0


# class DeliveryAttemptInline(uadmin.TabularInline):
#     model = DeliveryAttempt
#     form = DeliveryAttemptForm
#     extra = 0


# class ProofOfDeliveryInline(uadmin.StackedInline):
#     model = ProofOfDelivery
#     form = ProofOfDeliveryForm
#     extra = 0
#     max_num = 1
#     can_delete = True
#     fieldsets = (
#         ("Proof of Delivery", {
#             "fields": ("recipient_name", "signature", "photo"),
#             "classes": ("collapse",),
#         }),
#     )


# # -----------------
# # ModelAdmin registrations
# # -----------------
# @admin.register(Vehicle)
# class VehicleAdmin(uadmin.ModelAdmin):
#     form = VehicleForm
#     list_display = ("number_plate", "vehicle_type", "brand", "model", "capacity", "active")
#     search_fields = ("number_plate", "vehicle_type", "brand", "model")
#     list_filter = ("vehicle_type", "brand", "active")
#     readonly_fields = ("created", "updated")
#     fieldsets = (
#         ("Vehicle", {
#             "fields": (
#                 ( "number_plate", "vehicle_type",),
#                 ( "brand", "model", ),
#                 ("capacity", "remarks",)
#                 ),
#         }),
#         ("Timestamps", {
#             "fields": ("created", "updated"),
#             "classes": ("collapse",),
#         }),
#     )


# @admin.register(Rider)
# class RiderAdmin(uadmin.ModelAdmin):
#     form = RiderForm
#     list_display = ("full_name", "phone", "gender", "active")
#     search_fields = ("full_name", "phone", "license_number")
#     list_filter = ("gender", "active")
#     readonly_fields = ("created", "updated")
#     fieldsets = (
#         ("Identity", {
#             "fields": (("full_name", "phone",), ("gender", "date_of_birth", "address")),
#         }),
#         ("License & Notes", {
#             "fields": ("license_number", "remarks"),
#         }),
#         ("Timestamps", {
#             "fields": ("created", "updated"),
#             "classes": ("collapse",),
#         }),
#     )


# @admin.register(PickupRequest)
# class PickupRequestAdmin(uadmin.ModelAdmin):
#     form = PickupRequestForm
    
#     list_display = ( "client", "location", "requested_date", "time_window", "expected_packages", "status")
#     list_display_links=list_display
#     search_fields = ("location", "client__name")
#     list_filter = ("requested_date", "status")
#     date_hierarchy = "requested_date"
#     readonly_fields = ("created", "updated")
#     fieldsets = (
#         ("Request", {
#             "fields": (("client", "location",), ("requested_date", "time_window", "expected_packages",), "remarks"),
#         }),
#         ("Status", {
#             "fields": ("status",),
#         }),
         
#     )


# @admin.register(PickupOrder)
# class PickupOrderAdmin(uadmin.ModelAdmin):
#     form = PickupOrderForm
#     inlines = [PickupPackagesInline]
#     list_display = (
#         "id", "vendor", "sender_name", "from_location", "destination",
#         "service_type", "payment_method", "total_charge", "piece", "status",
#     )
#     search_fields = (
#         "from_location", "destination", "sender_name__name", "receiver_name",
#         "phone", "receiver_phone", "ref_no",
#     )
#     list_filter = ("service_type", "payment_method", "status")
#     readonly_fields = ("created", "updated")
#     fieldsets = (
#         ("Linkages", {
#             "fields": (("pickup_request", "vendor"),),
#         }),
#         ("Addresses", {
#             "fields": (("from_location", "destination"),),
#         }),
#         ("Sender", {
#             "fields": (("sender_name", "address"), ("phone", "alt_number")),
             
#         }),
#         ("Receiver", {
#             "fields": (("receiver_name", "receiver_address"), ("receiver_phone", "receiver_alt_no")),
             
#         }),
#         ("Service & Payment", {
#             "fields": (("service_type", "payment_method"), ("total_charge", "piece"), ("cod", "ref_no")),
#         }),
#         ("Notes", {
#             "fields": ("instruction", "remarks"),
#         }),
#         ("Status", {
#             "fields": ("status",),
#         }),
#         ("Timestamps", {
#             "fields": ("created", "updated"),
#             "classes": ("collapse",),
#         }),
#     )


# @admin.register(PickupPackages)
# class PickupPackagesAdmin(uadmin.ModelAdmin):
#     form = PickupPackagesForm
#     list_display = ("pickup_order", "weight", "weight_unit", "length", "bredth", "width", "length_unit")
#     search_fields = ("pickup_order__id",)
#     list_filter = ("weight_unit", "length_unit")
#     readonly_fields = ("created", "updated")
#     fieldsets = (
#         ("Package", {
#             "fields": ("pickup_order",( "weight", "weight_unit",), ("length", "bredth", "width", "length_unit"),),
#         }),
#         ("Timestamps", {
#             "fields": ("created", "updated"),
#             "classes": ("collapse",),
#         }),
#     )


# @admin.register(PickupRunsheet)
# class PickupRunsheetAdmin(uadmin.ModelAdmin):
#     form = PickupRunsheetForm
#     filter_horizontal = ("pickup_orders",)
#     list_display = ("id", "rider", "vehicle", "status")
#     search_fields = ("rider__full_name", "vehicle__number_plate")
#     list_filter = ("status",)
#     readonly_fields = ("created", "updated")
#     filter_horizontal = ["pickup_orders",]
#     fieldsets = (
#         ("Assignment", {
#             "fields": (("vehicle", "rider"),),
#         }),
#         ("Orders", {
#             "fields": ("pickup_orders",),
#         }),
#         ("Status", {
#             "fields": ("status",),
#         }),
#         ("Timestamps", {
#             "fields": ("created", "updated"),
#             "classes": ("collapse",),
#         }),
#     )


# @admin.register(DeliveryOrder)
# class DeliveryOrderAdmin(uadmin.ModelAdmin):
#     form = DeliveryOrderForm
#     inlines = [ProofOfDeliveryInline, DeliveryAttemptInline]
#     list_display = ("id", "pickup_order", "delivery_address", "delivery_status", "delivery_date", "delivered_by")
#     search_fields = ("delivery_address", "pickup_order__id", "delivered_by__full_name")
#     list_filter = ("delivery_status", "delivery_date")
#     date_hierarchy = "delivery_date"
#     readonly_fields = ("created", "updated")
#     fieldsets = (
#         ("Delivery", {
#             "fields": ("pickup_order", "delivery_address", "delivery_date", "delivered_by"),
#         }),
#         ("Status & Notes", {
#             "fields": ("delivery_status", "remarks"),
#         }),
#         ("Timestamps", {
#             "fields": ("created", "updated"),
#             "classes": ("collapse",),
#         }),
#     )


# @admin.register(DeliveryAttempt)
# class DeliveryAttemptAdmin(uadmin.ModelAdmin):
#     form = DeliveryAttemptForm
#     list_display = ("id", "delivery_order", "attempt_number", "status", "attempt_date")
#     search_fields = ("delivery_order__id",)
#     list_filter = ("status", "attempt_date")
#     readonly_fields = ("attempt_date",)
#     fieldsets = (
#         ("Attempt", {
#             "fields": ("delivery_order", "attempt_number", "status", "remarks"),
#         }),
#         ("Meta", {
#             "fields": ("attempt_date",),
#             "classes": ("collapse",),
#         }),
#     )


# @admin.register(ProofOfDelivery)
# class ProofOfDeliveryAdmin(uadmin.ModelAdmin):
#     form = ProofOfDeliveryForm
#     list_display = ("id", "delivery_order", "recipient_name", "delivery_time")
#     search_fields = ("delivery_order__id", "recipient_name")
#     readonly_fields = ("delivery_time",)
#     fieldsets = (
#         ("POD", {
#             "fields": ("delivery_order", "recipient_name", "signature", "photo"),
#         }),
#         ("Meta", {
#             "fields": ("delivery_time",),
#             "classes": ("collapse",),
#         }),
#     )


# @admin.register(DeliveryRunsheet)
# class DeliveryRunsheetAdmin(uadmin.ModelAdmin):
#     form = DeliveryRunsheetForm
#     filter_horizontal = ("delivery_orders",)
#     list_display = ("id", "rider", "vehicle", "run_date", "status")
#     search_fields = ("rider__full_name", "vehicle__number_plate")
#     list_filter = ("status", "run_date")
#     date_hierarchy = "run_date"
#     readonly_fields = ("created", "updated")
#     filter_horizontal = ["delivery_orders",]
#     fieldsets = (
#         ("Assignment", {
#             "fields": ("rider", "vehicle"),
#         }),
#         ("Orders", {
#             "fields": ("delivery_orders",),
#         }),
#         ("Run", {
#             "fields": ("run_date", "status", "remarks"),
#         }),
#         ("Timestamps", {
#             "fields": ("created", "updated"),
#             "classes": ("collapse",),
#         }),
#     )


# @admin.register(ReturnToVendor)
# class ReturnToVendorAdmin(uadmin.ModelAdmin):
#     form = ReturnToVendorForm
#     list_display = ("id", "vendor", "reference_order", "status", "processed_date")
#     search_fields = ("vendor__name", "reference_order__id")
#     list_filter = ("status", "processed_date")
#     date_hierarchy = "processed_date"
#     readonly_fields = ("created", "updated")
#     fieldsets = (
#         ("Return", {
#             "fields": ("vendor", "reference_order", "reason"),
#         }),
#         ("Status", {
#             "fields": ("status", "processed_date"),
#         }),
#         ("Timestamps", {
#             "fields": ("created", "updated"),
#             "classes": ("collapse",),
#         }),
#     )


# @admin.register(RtvBranchReturn)
# class RtvBranchReturnAdmin(uadmin.ModelAdmin):
#     form = RtvBranchReturnForm
#     list_display = ("id", "pickup_order", "from_branch", "to_branch", "status")
#     search_fields = ("pickup_order__id", "from_branch__name", "to_branch__name")
#     list_filter = ("status",)
#     readonly_fields = ("created", "updated")
#     fieldsets = (
#         ("RTV Branch Movement", {
#             "fields": ("pickup_order", "from_branch", "to_branch", "reason"),
#         }),
#         ("Status", {
#             "fields": ("status",),
#         }),
#         ("Timestamps", {
#             "fields": ("created", "updated"),
#             "classes": ("collapse",),
#         }),
#     )


# @admin.register(DispatchManifest)
# class DispatchManifestAdmin(uadmin.ModelAdmin):
#     form = DispatchManifestForm
#     filter_horizontal = ("orders",)
#     list_display = ("id", "rider", "vehicle", "dispatch_date", "status")
#     search_fields = ("rider__full_name", "vehicle__number_plate")
#     list_filter = ("status", "dispatch_date")
#     date_hierarchy = "dispatch_date"
#     readonly_fields = ("created", "updated")
#     fieldsets = (
#         ("Assignment", {
#             "fields": ("rider", "vehicle"),
#         }),
#         ("Orders", {
#             "fields": ("orders",),
#         }),
#         ("Dispatch", {
#             "fields": ("dispatch_date", "status"),
#         }),
#         ("Timestamps", {
#             "fields": ("created", "updated"),
#             "classes": ("collapse",),
#         }),
#     )


# @admin.register(ReceiveManifest)
# class ReceiveManifestAdmin(uadmin.ModelAdmin):
#     form = ReceiveManifestForm
#     filter_horizontal = ("orders",)
#     list_display = ("id", "from_branch", "to_branch", "receive_date", "status")
#     search_fields = ("from_branch__name", "to_branch__name")
#     list_filter = ("status", "receive_date")
#     date_hierarchy = "receive_date"
#     readonly_fields = ("created", "updated")
#     fieldsets = (
#         ("Movement", {
#             "fields": ("from_branch", "to_branch"),
#         }),
#         ("Orders", {
#             "fields": ("orders",),
#         }),
#         ("Receive", {
#             "fields": ("receive_date", "status"),
#         }),
#         ("Timestamps", {
#             "fields": ("created", "updated"),
#             "classes": ("collapse",),
#         }),
#     )
