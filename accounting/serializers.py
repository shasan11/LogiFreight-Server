# api/serializers.py
from django.db import transaction
from rest_framework import serializers
from .models import CashTransfer, CashTransferItems, JournalVoucher, JournalVoucherItems


class CashTransferItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashTransferItems
        fields = "__all__"
        read_only_fields = ("id", "uuid", "cash_transfer")


class CashTransferSerializer(serializers.ModelSerializer):
    items = CashTransferItemSerializer(many=True, required=False)

    class Meta:
        model = CashTransfer
        fields = "__all__"
        read_only_fields = ("id", "uuid")

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items", [])
        ct = CashTransfer.objects.create(**validated_data)
        for item in items:
            CashTransferItems.objects.create(cash_transfer=ct, **item)
        return ct

    @transaction.atomic
    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        if items is not None:
            instance.items.all().delete()
            for item in items:
                CashTransferItems.objects.create(cash_transfer=instance, **item)

        return instance


class JournalVoucherItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalVoucherItems
        fields = "__all__"
        read_only_fields = ("id", "uuid", "journal_voucher")


class JournalVoucherSerializer(serializers.ModelSerializer):
    items = JournalVoucherItemSerializer(many=True, required=False)

    class Meta:
        model = JournalVoucher
        fields = "__all__"
        read_only_fields = ("id", "uuid")

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items", [])
        jv = JournalVoucher.objects.create(**validated_data)
        for item in items:
            JournalVoucherItems.objects.create(journal_voucher=jv, **item)
        return jv

    @transaction.atomic
    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
