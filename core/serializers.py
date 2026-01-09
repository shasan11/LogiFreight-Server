from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer, UserSerializer as BaseUserSerializer
from django.contrib.auth.models import Group
from .models import CustomUser
from master.models import Branch


class BranchCoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"


class CustomUserCreateSerializer(BaseUserCreateSerializer):
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=False, allow_null=True)
    profile = serializers.ImageField(required=False, allow_null=True)
    groups = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), many=True, write_only=True, required=False)

    user_type = serializers.ChoiceField(choices=CustomUser.UserType.choices, required=True)
    customer = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=CustomUser._meta.get_field("customer").remote_field.model.objects.all())
    booking_agency = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=CustomUser._meta.get_field("booking_agency").remote_field.model.objects.all())
    carrier = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=CustomUser._meta.get_field("carrier").remote_field.model.objects.all())
    customs_agent = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=CustomUser._meta.get_field("customs_agent").remote_field.model.objects.all())

    class Meta(BaseUserCreateSerializer.Meta):
        model = CustomUser
        fields = (
            "id", "username", "email", "password",
            "first_name", "last_name",
            "branch", "profile",
            "user_type", "customer", "booking_agency", "carrier", "customs_agent",
            "groups",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user_type = attrs.get("user_type")

        mapping = {
            CustomUser.UserType.CUSTOMER: "customer",
            CustomUser.UserType.BOOKING_AGENCY: "booking_agency",
            CustomUser.UserType.CARRIER: "carrier",
            CustomUser.UserType.CUSTOMS_AGENT: "customs_agent",
        }
        field = mapping.get(user_type)

        for f in ("customer", "booking_agency", "carrier", "customs_agent"):
            if f != field:
                attrs[f] = None

        if field and attrs.get(field) is None:
            raise serializers.ValidationError({field: f"user_type='{user_type}' requires `{field}` to be set."})

        return attrs

    def create(self, validated_data):
        groups = validated_data.pop("groups", [])
        user = super().create(validated_data)
        if groups:
            user.groups.set(groups)
        return user


class CustomUserSerializer(BaseUserSerializer):
    profile_url = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = CustomUser
        fields = (
            "id", "username", "email",
            "first_name", "last_name",
            "branch",
            "user_type", "customer", "booking_agency", "carrier", "customs_agent",
            "profile_url", "profile",
            "groups",
            "is_active", "is_superuser",
        )

    def get_profile_url(self, obj):
        if obj.profile and hasattr(obj.profile, "url"):
            return obj.profile.url
        return None

    def get_groups(self, obj):
        return list(obj.groups.values_list("id", flat=True))
