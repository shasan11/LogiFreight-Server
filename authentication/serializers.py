# roles/serializers.py
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework import serializers

class PermissionSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ["id", "name", "codename", "content_type"]

    def get_content_type(self, obj):
        return f"{obj.content_type.app_label}.{obj.content_type.model}"

class RoleAssignUsersSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False
    )
    mode = serializers.ChoiceField(choices=["add", "remove", "set"], default="set")

class RoleSerializer(serializers.ModelSerializer):
    # Read nicely
    permissions = PermissionSerializer(many=True, read_only=True)
    # Write with IDs
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = Group
        fields = ["id", "name", "permissions", "permission_ids"]

    def create(self, validated_data):
        print("-------------------------------")
        print(validated_data)
        print("-------------------------------")
        perm_ids = validated_data.pop("permission_ids", [])
        group = Group.objects.create(**validated_data)
        if perm_ids:
            group.permissions.set(perm_ids)
        return group

    def update(self, instance, validated_data):
        perm_ids = validated_data.pop("permission_ids", None)
        instance.name = validated_data.get("name", instance.name)
        instance.save()
        if perm_ids is not None:
            instance.permissions.set(perm_ids)
        return instance
