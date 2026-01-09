from django import forms
from unfold import widgets as UW

from .models import (
    Vehicle,
    Rider,
    PickupRequest,
    PickupOrder,
    PickupPackages,
    PickupRunsheet,
    DeliveryOrder,
    DeliveryAttempt,
    ProofOfDelivery,
    DeliveryRunsheet,
    ReturnToVendor,
    RtvBranchReturn,
    DispatchManifest,
    ReceiveManifest,
)

# -----------------
# Unfold Admin Widgets
# -----------------
DATE_INPUT = UW.UnfoldAdminDateWidget()
DATETIME_INPUT = UW.UnfoldAdminSplitDateTimeWidget(attrs={"type": "datetime-local"})
NUMBER_INPUT = UW.UnfoldAdminIntegerFieldWidget(attrs={"step": "0.01"})
INT_INPUT = UW.UnfoldAdminIntegerFieldWidget(attrs={"step": "1"})
TEXT_INPUT = UW.UnfoldAdminTextInputWidget()
TEXTAREA = UW.UnfoldAdminTextareaWidget(attrs={"rows": 2})
FILE_INPUT = UW.UnfoldAdminFileFieldWidget()
SELECT = UW.UnfoldAdminSelectWidget()
SELECT_MULTI = UW.UnfoldAdminSelectMultipleWidget()
RADIO_SELECT = UW.UnfoldAdminRadioSelectWidget()
BOOLEAN=UW.UnfoldBooleanSwitchWidget()


class BasePlaceholderModelForm(forms.ModelForm):
    """
    Auto-add placeholder=label to each field if not explicitly set.
    Also adds 'w-full' class for Unfold/Tailwind-friendly width.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            # Add placeholder if applicable
            if hasattr(widget, "attrs") and "placeholder" not in widget.attrs:
                widget.attrs["placeholder"] = field.label or name.replace("_", " ").title()
            # Ensure full width class for consistency
            classes = widget.attrs.get("class", "")
            if "w-full" not in classes:
                widget.attrs["class"] = (classes + " w-full").strip()


# -----------------
# Forms
# -----------------
class VehicleForm(BasePlaceholderModelForm):
    class Meta:
        model = Vehicle
        exclude = ("id", "created", "updated", "user_add", "history", "active", "branch")
        widgets = {
            "number_plate": TEXT_INPUT,
            "vehicle_type": TEXT_INPUT,
            "brand": TEXT_INPUT,
            "model": TEXT_INPUT,
            "capacity": INT_INPUT,
            "remarks": TEXTAREA,
        }


class RiderForm(BasePlaceholderModelForm):
    class Meta:
        model = Rider
        exclude = ("id", "created", "updated", "user_add", "history", "active", "branch")
        widgets = {
            "full_name": TEXT_INPUT,
            "phone": TEXT_INPUT,
            "gender": RADIO_SELECT,  # has choices
            "date_of_birth": DATE_INPUT,
            "address": TEXTAREA,
            "license_number": TEXT_INPUT,
            "remarks": TEXTAREA,
        }


class PickupRequestForm(BasePlaceholderModelForm):
    class Meta:
        model = PickupRequest
        exclude = ("id", "uuid", "created", "updated", "user_add", "history", "active", "branch")
        widgets = {
            "client": SELECT,
            "location": TEXT_INPUT,
            "requested_date": DATE_INPUT,
            "time_window": TEXT_INPUT,
            "expected_packages": INT_INPUT,
            "remarks": TEXTAREA,
            "status": SELECT,
        }


class PickupOrderForm(BasePlaceholderModelForm):
    class Meta:
        model = PickupOrder
        exclude = ("id", "uuid", "created", "updated", "user_add", "history", "active", "branch")
        widgets = {
            "pickup_request": SELECT,
            "vendor": SELECT,
            "from_location": TEXT_INPUT,
            "destination": TEXT_INPUT,
            "sender_name": SELECT,
            "address": TEXT_INPUT,
            "phone": TEXT_INPUT,
            "alt_number": TEXT_INPUT,
            "receiver_name": TEXT_INPUT,
            "receiver_address": TEXT_INPUT,
            "receiver_phone": TEXT_INPUT,
            "receiver_alt_no": TEXT_INPUT,
            "service_type": TEXT_INPUT,
            "payment_method": TEXT_INPUT,
            "total_charge": NUMBER_INPUT,
            "piece": INT_INPUT,
            "cod": NUMBER_INPUT,
            "ref_no": TEXT_INPUT,
            "instruction": TEXTAREA,
            "remarks": TEXTAREA,
            "status": SELECT,
        }


class PickupPackagesForm(BasePlaceholderModelForm):
    class Meta:
        model = PickupPackages
        exclude = ("id", "uuid", "created", "updated", "user_add", "history", "active", "branch")
        widgets = {
            "good_description": TEXT_INPUT,
            "fragile": BOOLEAN, 
            "pickup_order": SELECT,
            "weight": NUMBER_INPUT,
            "weight_unit": SELECT,
            "length": NUMBER_INPUT,
            "bredth": NUMBER_INPUT,
            "width": NUMBER_INPUT,
            "length_unit": SELECT,
        }


class PickupRunsheetForm(BasePlaceholderModelForm):
    class Meta:
        model = PickupRunsheet
        exclude = ("id", "uuid", "created", "updated", "user_add", "history", "active", "branch")
        widgets = {
            "vehicle": SELECT,
            "rider": SELECT,
             
            "status": SELECT,
        }


class DeliveryOrderForm(BasePlaceholderModelForm):
    class Meta:
        model = DeliveryOrder
        exclude = ("id", "uuid", "created", "updated", "user_add", "history", "active", "branch")
        widgets = {
            "pickup_order": SELECT,
            "delivery_address": TEXT_INPUT,
            "delivery_status": TEXT_INPUT,
            "delivery_date": DATE_INPUT,
            "delivered_by": SELECT,
            "remarks": TEXTAREA,
        }


class DeliveryAttemptForm(BasePlaceholderModelForm):
    class Meta:
        model = DeliveryAttempt
        exclude = ("id", "attempt_date", "user_add", "history")
        widgets = {
            "delivery_order": SELECT,
            "attempt_number": INT_INPUT,
            "status": TEXT_INPUT,
            "remarks": TEXTAREA,
        }


class ProofOfDeliveryForm(BasePlaceholderModelForm):
    class Meta:
        model = ProofOfDelivery
        exclude = ("id", "delivery_time", "user_add", "history")
        widgets = {
            "delivery_order": SELECT,
            "recipient_name": TEXT_INPUT,
            "signature": FILE_INPUT,
            "photo": FILE_INPUT,
        }


class DeliveryRunsheetForm(BasePlaceholderModelForm):
    class Meta:
        model = DeliveryRunsheet
        exclude = ("id", "uuid", "created", "updated", "user_add", "history", "active", "branch")
        widgets = {
            "rider": SELECT,
            "vehicle": SELECT,
            #"delivery_orders": SELECT_MULTI,
            "run_date": DATE_INPUT,
            "status": TEXT_INPUT,
            "remarks": TEXTAREA,
        }


class ReturnToVendorForm(BasePlaceholderModelForm):
    class Meta:
        model = ReturnToVendor
        exclude = ("id", "uuid", "created", "updated", "user_add", "history", "active", "branch")
        widgets = {
            "vendor": SELECT,
            "reference_order": SELECT,
            "reason": TEXTAREA,
            "status": TEXT_INPUT,
            "processed_date": DATE_INPUT,
        }


class RtvBranchReturnForm(BasePlaceholderModelForm):
    class Meta:
        model = RtvBranchReturn
        exclude = ("id", "uuid", "created", "updated", "user_add", "history", "active")
        widgets = {
            "pickup_order": SELECT,
            "from_branch": SELECT,
            "to_branch": SELECT,
            "reason": TEXTAREA,
            "status": TEXT_INPUT,
        }


class DispatchManifestForm(BasePlaceholderModelForm):
    class Meta:
        model = DispatchManifest
        exclude = ("id", "uuid", "created", "updated", "user_add", "history", "active", "branch")
        widgets = {
            "rider": SELECT,
            "vehicle": SELECT,
            "orders": SELECT_MULTI,
            "dispatch_date": DATE_INPUT,
            "status": TEXT_INPUT,
        }


class ReceiveManifestForm(BasePlaceholderModelForm):
    class Meta:
        model = ReceiveManifest
        exclude = ("id", "uuid", "created", "updated", "user_add", "history", "active", "branch")
        widgets = {
            "from_branch": SELECT,
            "to_branch": SELECT,
            "orders": SELECT_MULTI,
            "receive_date": DATE_INPUT,
            "status": TEXT_INPUT,
        }