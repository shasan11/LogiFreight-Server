# admin.py (users app)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(DjangoUserAdmin):
    """
    Custom admin for CustomUser where USERNAME_FIELD = email.
    NO autocomplete_fields used.
    """

    # List page
    list_display = (
        "email",
        "username",
        "user_type",
        "branch",
        "is_staff",
        "is_active",
        "is_superuser",
        "last_login",
        "date_joined",
    )
    list_filter = ("user_type", "branch", "is_staff", "is_active", "is_superuser")
    ordering = ("email",)
    search_fields = ("email", "username", "first_name", "last_name")

    # Readonly
    readonly_fields = ("last_login", "date_joined")

    # Edit page layout
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("username", "first_name", "last_name", "profile")}),
        (
            _("User Type Links"),
            {
                "fields": (
                    "user_type",
                    "customer",
                    "booking_agency",
                    "carrier",
                    "customs_agent",
                    "branch",
                )
            },
        ),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    # Add user page layout
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "user_type",
                    "customer",
                    "booking_agency",
                    "carrier",
                    "customs_agent",
                    "branch",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )

    # This helps admin know what field to use as "login" identifier in UI
    # (DjangoUserAdmin uses these in forms)
    def get_fieldsets(self, request, obj=None):
        return super().get_fieldsets(request, obj)

    def save_model(self, request, obj, form, change):
        """
        Enforce your model.clean() in admin so the wrong link combo can't be saved.
        Also ensures your clean() nulls the non-selected relations.
        """
        obj.full_clean()
        super().save_model(request, obj, form, change)
