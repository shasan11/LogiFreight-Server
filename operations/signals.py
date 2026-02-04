from __future__ import annotations

from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from operations.models import ShipmentPackages
from warehouse.models import HandlingUnit


def _handling_unit_base_data(package: ShipmentPackages) -> dict:
    return {
        "shipment": package.shipment,
        "hu_code": f"{package.shipment_package}-HU",
        "gross_weight": package.gross_weight or 0,
        "weight_uom": package.mass_unit,
        "volume_uom": package.package_unit,
    }


def _assign_package_to_units(package: ShipmentPackages, units: list[HandlingUnit]) -> None:
    for unit in units:
        unit.packages.add(package)


def _get_existing_units(package: ShipmentPackages) -> list[HandlingUnit]:
    return list(
        HandlingUnit.objects.filter(packages=package, shipment=package.shipment).order_by("created")
    )


def _sync_handling_units(package: ShipmentPackages) -> None:
    desired_quantity = int(package.quantity or 0)
    if desired_quantity < 0:
        desired_quantity = 0

    existing_units = _get_existing_units(package)
    current_quantity = len(existing_units)
    if current_quantity == desired_quantity:
        return

    base_data = _handling_unit_base_data(package)
    if desired_quantity > current_quantity:
        units_to_create = [
            HandlingUnit.objects.create(**base_data) for _ in range(desired_quantity - current_quantity)
        ]
        _assign_package_to_units(package, units_to_create)
        return

    units_to_delete = existing_units[desired_quantity:]
    if units_to_delete:
        HandlingUnit.objects.filter(id__in=[unit.id for unit in units_to_delete]).delete()


@receiver(pre_save, sender=ShipmentPackages)
def _cache_old_package_quantity(sender, instance: ShipmentPackages, **kwargs) -> None:
    if not instance.pk:
        instance._previous_quantity = 0
        return

    existing = ShipmentPackages.objects.filter(pk=instance.pk).only("quantity").first()
    instance._previous_quantity = int(existing.quantity) if existing else 0


@receiver(post_save, sender=ShipmentPackages)
def _sync_package_handling_units(sender, instance: ShipmentPackages, created: bool, **kwargs) -> None:
    transaction.on_commit(lambda: _sync_handling_units(instance))


@receiver(post_delete, sender=ShipmentPackages)
def _delete_package_handling_units(sender, instance: ShipmentPackages, **kwargs) -> None:
    HandlingUnit.objects.filter(packages=instance).delete()


def register_operations_signals() -> None:
    # Imported for side effects to connect receivers.
    return None
