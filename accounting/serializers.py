# api/serializers.py
from django.db import transaction
from rest_framework import serializers

from core.utils.AdaptedBulkListSerializer import BulkModelSerializer

from .models import (
    ChartofAccounts,
    BankAccounts,
    Currency,
    PaymentMethod,
    GeneralLedger,
    JournalVoucher,
    JournalVoucherItems,
    ChequeRegister,
    CashTransfer,
    CashTransferItems,
)


# -----------------------------
# Simple (leaf) serializers
# -----------------------------
class ChartofAccountsSerializer(BulkModelSerializer):
    class Meta:
        model = ChartofAccounts
        fields = "__all__"


class CurrencySerializer(BulkModelSerializer):
    class Meta:
        model = Currency
        fields = "__all__"


class PaymentMethodSerializer(BulkModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = "__all__"
        read_only_fields = ("id", "uuid")


class BankAccountsSerializer(BulkModelSerializer):
    class Meta:
        model = BankAccounts
        fields = "__all__"
        read_only_fields = ("id", "uuid")


class GeneralLedgerSerializer(BulkModelSerializer):
    class Meta:
        model = GeneralLedger
        fields = "__all__"
        read_only_fields = ("id", "uuid")


# -----------------------------
# Nested: Journal Voucher
# -----------------------------
class JournalVoucherItemSerializer(BulkModelSerializer):
    class Meta:
        model = JournalVoucherItems
        fields = "__all__"
        read_only_fields = ("id", "uuid", "journal_voucher")


class JournalVoucherSerializer(BulkModelSerializer):
    items = JournalVoucherItemSerializer(many=True, required=False)

    class Meta:
        model = JournalVoucher
        fields = "__all__"
        read_only_fields = ("id", "uuid")

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items", [])
        jv = JournalVoucher.objects.create(**validated_data)
        if items:
            JournalVoucherItems.objects.bulk_create(
                [JournalVoucherItems(journal_voucher=jv, **it) for it in items]
            )
        return jv

    @transaction.atomic
    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        if items is not None:
            instance.items.all().delete()
            if items:
                JournalVoucherItems.objects.bulk_create(
                    [JournalVoucherItems(journal_voucher=instance, **it) for it in items]
                )
        return instance


# -----------------------------
# Nested: Cash Transfer
# -----------------------------
class CashTransferItemSerializer(BulkModelSerializer):
    class Meta:
        model = CashTransferItems
        fields = "__all__"
        read_only_fields = ("id", "uuid", "cash_transfer")


class CashTransferSerializer(BulkModelSerializer):
    items = CashTransferItemSerializer(many=True, required=False)

    class Meta:
        model = CashTransfer
        fields = "__all__"
        read_only_fields = ("id", "uuid")

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items", [])
        ct = CashTransfer.objects.create(**validated_data)
        if items:
            CashTransferItems.objects.bulk_create(
                [CashTransferItems(cash_transfer=ct, **it) for it in items]
            )
        return ct

    @transaction.atomic
    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        if items is not None:
            instance.items.all().delete()
            if items:
                CashTransferItems.objects.bulk_create(
                    [CashTransferItems(cash_transfer=instance, **it) for it in items]
                )
        return instance


# -----------------------------
# Cheque Register
# -----------------------------
class ChequeRegisterSerializer(BulkModelSerializer):
    class Meta:
        model = ChequeRegister
        fields = "__all__"
        read_only_fields = ("id", "uuid")
