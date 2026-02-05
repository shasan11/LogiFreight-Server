# purchase/serializers.py
from django.db import transaction
from rest_framework import serializers

from .models import (
    VendorBillsGroup, ExpenseCategory, Expenses, ExpensesItems,
    VendorBills, VendorBillItems,
    VendorPayments, VendorPaymentEntries,
)


class VendorBillsGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorBillsGroup
        fields = "__all__"
        read_only_fields = ("created", "updated", "user_add", "history")


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = "__all__"
        read_only_fields = ("created", "updated", "user_add", "history")


class ExpensesItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpensesItems
        fields = "__all__"
        read_only_fields = ("id",)

    def validate(self, attrs):
        rate = attrs.get("rate", getattr(self.instance, "rate", 0))
        qty = attrs.get("quantity", getattr(self.instance, "quantity", 0))
        if rate is not None and rate < 0:
            raise serializers.ValidationError({"rate": "Must be >= 0"})
        if qty is not None and qty < 0:
            raise serializers.ValidationError({"quantity": "Must be >= 0"})
        return attrs


class ExpensesSerializer(serializers.ModelSerializer):
    expenses_items = ExpensesItemsSerializer(many=True, required=False)

    class Meta:
        model = Expenses
        fields = "__all__"
        read_only_fields = ("created", "updated", "user_add", "history", "subtotal_amount", "taxable_amount", "non_taxable_amount", "total_amount", "paid_amount", "remaining_amount")

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("expenses_items", [])
        obj = Expenses.objects.create(**validated_data)
        for it in items:
            ExpensesItems.objects.create(expenses=obj, **it)
        obj.recalc_from_items(save=True)
        obj.update_status(save=True)
        return obj

    @transaction.atomic
    def update(self, instance, validated_data):
        items = validated_data.pop("expenses_items", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        if items is not None:
            existing = {str(x.id): x for x in instance.expenses_items.all()}
            keep_ids = set()

            for it in items:
                it_id = str(it.get("id")) if it.get("id") else None
                if it_id and it_id in existing:
                    obj = existing[it_id]
                    for k, v in it.items():
                        if k != "id":
                            setattr(obj, k, v)
                    obj.save()
                    keep_ids.add(it_id)
                else:
                    new = ExpensesItems.objects.create(expenses=instance, **{k: v for k, v in it.items() if k != "id"})
                    keep_ids.add(str(new.id))

            for ex_id, ex_obj in existing.items():
                if ex_id not in keep_ids:
                    ex_obj.delete()

        instance.recalc_from_items(save=True)
        instance.update_status(save=True)
        return instance


class VendorBillItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorBillItems
        fields = "__all__"
        read_only_fields = ("id",)


class VendorBillsSerializer(serializers.ModelSerializer):
    bill_items = VendorBillItemsSerializer(many=True, required=False)

    class Meta:
        model = VendorBills
        fields = "__all__"
        read_only_fields = ("created", "updated", "user_add", "history", "subtotal_amount", "taxable_amount", "non_taxable_amount", "total_amount", "paid_amount", "remaining_amount")

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("bill_items", [])
        obj = VendorBills.objects.create(**validated_data)
        for it in items:
            VendorBillItems.objects.create(vendorbills=obj, **it)
        obj.recalc_from_items(save=True)
        obj.update_status(save=True)
        return obj

    @transaction.atomic
    def update(self, instance, validated_data):
        items = validated_data.pop("bill_items", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        if items is not None:
            existing = {str(x.id): x for x in instance.bill_items.all()}
            keep_ids = set()

            for it in items:
                it_id = str(it.get("id")) if it.get("id") else None
                if it_id and it_id in existing:
                    obj = existing[it_id]
                    for k, v in it.items():
                        if k != "id":
                            setattr(obj, k, v)
                    obj.save()
                    keep_ids.add(it_id)
                else:
                    new = VendorBillItems.objects.create(vendorbills=instance, **{k: v for k, v in it.items() if k != "id"})
                    keep_ids.add(str(new.id))

            for ex_id, ex_obj in existing.items():
                if ex_id not in keep_ids:
                    ex_obj.delete()

        instance.recalc_from_items(save=True)
        instance.update_status(save=True)
        return instance


class VendorPaymentEntriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorPaymentEntries
        fields = "__all__"
        read_only_fields = ("id",)


class VendorPaymentsSerializer(serializers.ModelSerializer):
    payment_entries = VendorPaymentEntriesSerializer(many=True, required=False)

    class Meta:
        model = VendorPayments
        fields = "__all__"
        read_only_fields = ("created", "updated", "user_add", "history", "amount")

    @transaction.atomic
    def create(self, validated_data):
        entries = validated_data.pop("payment_entries", [])
        obj = VendorPayments.objects.create(**validated_data)
        for e in entries:
            VendorPaymentEntries.objects.create(vendor_payments=obj, **e)
        obj.recalc_amount(save=True)
        return obj

    @transaction.atomic
    def update(self, instance, validated_data):
        entries = validated_data.pop("payment_entries", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        if entries is not None:
            existing = {str(x.id): x for x in instance.payment_entries.all()}
            keep_ids = set()

            for e in entries:
                e_id = str(e.get("id")) if e.get("id") else None
                if e_id and e_id in existing:
                    obj = existing[e_id]
                    for k, v in e.items():
                        if k != "id":
                            setattr(obj, k, v)
                    obj.save()
                    keep_ids.add(e_id)
                else:
                    new = VendorPaymentEntries.objects.create(vendor_payments=instance, **{k: v for k, v in e.items() if k != "id"})
                    keep_ids.add(str(new.id))

            for ex_id, ex_obj in existing.items():
                if ex_id not in keep_ids:
                    ex_obj.delete()

        instance.recalc_amount(save=True)
        return instance
