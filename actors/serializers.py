from __future__ import annotations
from rest_framework import serializers
from actors.models import (
    BookingAgency, Carrier, CustomsAgent, Vendor,
    Customer, CustomerPerson, CustomerCompany,
    Department, Designation, Employee, MainActor
)


class BulkListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        model = self.child.Meta.model
        objs = [model(**item) for item in validated_data]
        return model.objects.bulk_create(objs)

    def update(self, instance, validated_data):
        instance_map = {str(obj.id): obj for obj in instance}
        updated = []
        for item in validated_data:
            obj = instance_map.get(str(item.get("id")))
            if not obj:
                continue
            for attr, value in item.items():
                if attr != "id":
                    setattr(obj, attr, value)
            updated.append(obj)
        if updated:
            updated[0].__class__.objects.bulk_update(updated, fields=[f for f in validated_data[0].keys() if f != "id"])
        return updated


class BulkModelSerializer(serializers.ModelSerializer):
    class Meta:
        list_serializer_class = BulkListSerializer


class BookingAgencySerializer(BulkModelSerializer):
    class Meta:
        model = BookingAgency
        fields = "__all__"


class CarrierSerializer(BulkModelSerializer):
    class Meta:
        model = Carrier
        fields = "__all__"


class CustomsAgentSerializer(BulkModelSerializer):
    class Meta:
        model = CustomsAgent
        fields = "__all__"


class VendorSerializer(BulkModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"


class CustomerPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerPerson
        fields = "__all__"


class CustomerCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerCompany
        fields = "__all__"


class CustomerSerializer(BulkModelSerializer):
    person = CustomerPersonSerializer(required=False, allow_null=True)
    company = CustomerCompanySerializer(required=False, allow_null=True)

    class Meta:
        model = Customer
        fields = "__all__"

    def create(self, validated_data):
        person_data = validated_data.pop("person", None)
        company_data = validated_data.pop("company", None)
        obj = super().create(validated_data)
        if obj.customer_type == Customer.CustomerType.PERSON and person_data:
            CustomerPerson.objects.update_or_create(customer=obj, defaults=person_data)
        if obj.customer_type == Customer.CustomerType.COMPANY and company_data:
            CustomerCompany.objects.update_or_create(customer=obj, defaults=company_data)
        return obj

    def update(self, instance, validated_data):
        person_data = validated_data.pop("person", None)
        company_data = validated_data.pop("company", None)
        obj = super().update(instance, validated_data)
        if obj.customer_type == Customer.CustomerType.PERSON and person_data is not None:
            CustomerPerson.objects.update_or_create(customer=obj, defaults=person_data)
        if obj.customer_type == Customer.CustomerType.COMPANY and company_data is not None:
            CustomerCompany.objects.update_or_create(customer=obj, defaults=company_data)
        return obj


class DepartmentSerializer(BulkModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"


class DesignationSerializer(BulkModelSerializer):
    class Meta:
        model = Designation
        fields = "__all__"


class EmployeeSerializer(BulkModelSerializer):
    class Meta:
        model = Employee
        fields = "__all__"


class MainActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainActor
        fields = "__all__"
        read_only_fields = ["actor_type", "display_name"]
