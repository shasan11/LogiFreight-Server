from django.db import transaction
from rest_framework import serializers

from .models import Sales, SalesItem, CustomerPayment, CustomerPaymentItems


class SalesItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesItem
        fields = "__all__"
        read_only_fields = ("id",)


class SalesSerializer(serializers.ModelSerializer):
    items = SalesItemSerializer(many=True, required=False)

    class Meta:
        model = Sales
        fields = "__all__"
        read_only_fields = (
            "created",
            "updated",
            "user_add",
            "history",
            "total",
            "paid_amount",
            "balance_due",
        )

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items", [])
        sale = Sales.objects.create(**validated_data)
        for item in items:
            SalesItem.objects.create(sales=sale, **item)
        sale.recompute_totals(save_self=True)
        return sale

    @transaction.atomic
    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        if items is not None:
            existing = {str(obj.id): obj for obj in instance.items.all()}
            keep_ids = set()
            for item in items:
                item_id = str(item.get("id")) if item.get("id") else None
                if item_id and item_id in existing:
                    obj = existing[item_id]
                    for key, value in item.items():
                        if key != "id":
                            setattr(obj, key, value)
                    obj.save()
                    keep_ids.add(item_id)
                else:
                    new_obj = SalesItem.objects.create(
                        sales=instance,
                        **{key: value for key, value in item.items() if key != "id"},
                    )
                    keep_ids.add(str(new_obj.id))

            for existing_id, existing_obj in existing.items():
                if existing_id not in keep_ids:
                    existing_obj.delete()

        instance.recompute_totals(save_self=True)
        return instance


class CustomerPaymentItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerPaymentItems
        fields = "__all__"
        read_only_fields = ("id",)


class CustomerPaymentSerializer(serializers.ModelSerializer):
    allocations = CustomerPaymentItemsSerializer(many=True, required=False)

    class Meta:
        model = CustomerPayment
        fields = "__all__"
        read_only_fields = ("created", "updated", "user_add", "history")

    @transaction.atomic
    def create(self, validated_data):
        allocations = validated_data.pop("allocations", [])
        payment = CustomerPayment.objects.create(**validated_data)
        for allocation in allocations:
            CustomerPaymentItems.objects.create(customerpayment=payment, **allocation)
        return payment

    @transaction.atomic
    def update(self, instance, validated_data):
        allocations = validated_data.pop("allocations", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        if allocations is not None:
            existing = {str(obj.id): obj for obj in instance.allocations.all()}
            keep_ids = set()
            for allocation in allocations:
                allocation_id = str(allocation.get("id")) if allocation.get("id") else None
                if allocation_id and allocation_id in existing:
                    obj = existing[allocation_id]
                    for key, value in allocation.items():
                        if key != "id":
                            setattr(obj, key, value)
                    obj.save()
                    keep_ids.add(allocation_id)
                else:
                    new_obj = CustomerPaymentItems.objects.create(
                        customerpayment=instance,
                        **{key: value for key, value in allocation.items() if key != "id"},
                    )
                    keep_ids.add(str(new_obj.id))

            for existing_id, existing_obj in existing.items():
                if existing_id not in keep_ids:
                    existing_obj.delete()

        return instance
