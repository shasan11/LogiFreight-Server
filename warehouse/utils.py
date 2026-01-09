from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from warehouse.models import Inventory, InventoryMove, HandlingUnit, Location


STATUS_BY_MOVE = {
    "RECEIVE": HandlingUnit.HUStatus.RECEIVED,
    "QC": HandlingUnit.HUStatus.QC_HOLD,
    "PUTAWAY": HandlingUnit.HUStatus.STORED,
    "ALLOCATE": HandlingUnit.HUStatus.ALLOCATED,
    "PICK": HandlingUnit.HUStatus.PICKED,
    "PACK": HandlingUnit.HUStatus.PACKED,
    "STAGE": HandlingUnit.HUStatus.STAGED,
    "LOAD": HandlingUnit.HUStatus.LOADED,
    "DISPATCH": HandlingUnit.HUStatus.DISPATCHED,
}


@transaction.atomic
def ensure_inventory(handling_unit: HandlingUnit, location: Location | None, branch=None, user=None) -> Inventory:
    inv, _ = Inventory.objects.select_for_update().get_or_create(
        handling_unit=handling_unit,
        defaults={"location": location, "on_hand": True, "last_moved_at": timezone.now(), "branch": branch, "user_add": user},
    )
    if location and inv.location_id != location.id:
        inv.location = location
        inv.last_moved_at = timezone.now()
        if branch is not None:
            inv.branch = branch
        if user is not None:
            inv.user_add = user
        inv.save(update_fields=["location", "last_moved_at", "branch", "user_add", "updated"])
    return inv


@transaction.atomic
def log_move(
    *,
    handling_unit: HandlingUnit,
    move_type: str,
    from_location: Location | None = None,
    to_location: Location | None = None,
    branch=None,
    user=None,
    ref: str | None = None,
    note: str | None = None,
    moved_at=None,
) -> InventoryMove:
    moved_at = moved_at or timezone.now()
    move = InventoryMove.objects.create(
        handling_unit=handling_unit,
        move_type=move_type,
        from_location=from_location,
        to_location=to_location,
        ref=ref,
        note=note,
        moved_at=moved_at,
        branch=branch,
        user_add=user,
        active=True,
    )
    if to_location:
        ensure_inventory(handling_unit, to_location, branch=branch, user=user)
    if move_type in STATUS_BY_MOVE:
        new_status = STATUS_BY_MOVE[move_type]
        if handling_unit.status != new_status:
            handling_unit.status = new_status
            handling_unit.save(update_fields=["status", "updated"])
    return move
