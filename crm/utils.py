from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from django.db import transaction

from crm.models import Quotation


def _to_int_set(ids: Iterable[int | str | None]) -> set[int]:
    out: set[int] = set()
    for x in ids:
        if x is None:
            continue
        try:
            out.add(int(x))
        except (TypeError, ValueError):
            continue
    return out


def recompute_quotations(quotation_ids: Iterable[int | str | None]) -> None:
    ids = _to_int_set(quotation_ids)
    if not ids:
        return

    def _run():
        qs = Quotation.objects.filter(id__in=ids)
        for q in qs:
            q.recompute_totals()
            q.save(update_fields=[
                "subtotal_charge",
                "tax_total_charge",
                "total_charge",
                "subtotal_invoice",
                "tax_total_invoice",
                "total_invoice",
                "updated",
            ])

    transaction.on_commit(_run)
