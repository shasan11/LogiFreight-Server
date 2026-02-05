# operations/services/invoicing.py
from __future__ import annotations

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from operations.models import Shipment, PaymentSummary, ShipmentCharges
from sales.models import Sales, SalesItem
from accounting.models import Currency
from actors.models import Customer


def _vat_code_from_tax_rate(tax_rate: Decimal) -> str:
    tr = Decimal(tax_rate or 0)
    if tr == Decimal("13.00"):
        return "thirteen_vat"
    if tr == Decimal("0.00"):
        return "zero_vat"
    return "no_vat"


@transaction.atomic
def generate_invoice_from_shipment(
    *,
    shipment_id: int,
    customer_id: int,
    currency_id: int,
    reference: str | None = None,
    invoice_date=None,
    due_date=None,
    auto_finalize_no: bool = False,
) -> Sales:
    shipment = Shipment.objects.select_for_update().get(pk=shipment_id)
    customer = Customer.objects.get(pk=customer_id)
    currency = Currency.objects.get(pk=currency_id)

    ps = PaymentSummary.objects.select_for_update().filter(shipment=shipment).first()
    if not ps:
        raise ValidationError("PaymentSummary not found for this shipment.")

    charges = list(
        ShipmentCharges.objects.select_for_update()
        .filter(payment_summary=ps, active=True, is_invoiced=False)
        .order_by("id")
    )
    if not charges:
        raise ValidationError("No uninvoiced shipment charges found.")

    inv = Sales.objects.create(
        branch=shipment.branch,
        customer=customer,
        currency=currency,
        reference=reference,
        shipment=shipment,
        invoice_date=invoice_date or timezone.localdate(),
        due_date=due_date,
        status="draft",
        po_date=timezone.localdate(),
    )

    for ch in charges:
        vat_code = _vat_code_from_tax_rate(ch.tax_rate)

        item = SalesItem.objects.create(
            branch=shipment.branch,
            sales=inv,
            shipment_charge=ch,
            item_name=ch.charge_name,
            quantity=ch.qty,
            rate=ch.unit_price_invoice,
            vat=vat_code,
            discount_percent=Decimal("0.00"),
        )

        ch.mark_invoiced(inv, item)

    inv.refresh_from_db()

    # keep profitability updated (sell/buy/profit)
    ps.recompute_from_lines(save=True)

    if auto_finalize_no:
        inv.finalize_number_if_needed("INV")

    return inv
