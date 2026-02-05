# app_name/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import PickupOrder, DeliveryOrder


def _map_delivery_status(pickup_status: str) -> str:
    """
    Map PickupOrder.status (PICKUP_REQUEST_STATUS) to DeliveryOrder.delivery_status.
    Adjust this mapping as your business flow evolves.
    """
    status = (pickup_status or "").upper()

    # Common normalizations
    mapping = {
        "DRAFT": "PENDING",
        "PENDING": "PENDING",
        "CONFIRMED": "PENDING",
        "ASSIGNED": "OUT_FOR_DELIVERY",
        "IN_TRANSIT": "OUT_FOR_DELIVERY",
        "ARRIVED": "OUT_FOR_DELIVERY",
        "PICKED_UP": "OUT_FOR_DELIVERY",
        "FAILED": "FAILED",
        "CANCELLED": "CANCELLED",
        "COMPLETED": "DELIVERED",
        "RESCHEDULED": "PENDING",
        "ON_HOLD": "PENDING",
        "PARTIALLY_PICKED": "OUT_FOR_DELIVERY",
        # Fallbacks often seen in this codebase:
        "CREATED": "PENDING",
        "RECEIVED": "PENDING",
        "DISPATCHED": "OUT_FOR_DELIVERY",
    }
    return mapping.get(status, "PENDING")


def _derive_delivery_address(instance: PickupOrder) -> str:
    """
    Prefer the receiver's full address, fall back to destination (hub/city),
    and finally the sender's address if nothing else is present.
    """
    return (
        (instance.receiver_address or "").strip()
        or (instance.destination or "").strip()
        or (instance.sender_address or "").strip()
        or ""
    )


def _sync_fields_from_pickup_to_delivery(instance: PickupOrder, delivery: DeliveryOrder) -> bool:
    """
    Copy relevant fields from PickupOrder to DeliveryOrder.
    Returns True if any field changed, False otherwise (to avoid extra saves).
    """
    changed = False

    # Address & basic linkage
    new_address = _derive_delivery_address(instance)
    if delivery.delivery_address != new_address:
        delivery.delivery_address = new_address
        changed = True

    # Status mapping
    new_status = _map_delivery_status(instance.status)
    if delivery.delivery_status != new_status:
        delivery.delivery_status = new_status
        changed = True

    # When marked delivered, set delivery_date if not set
    if new_status == "DELIVERED" and delivery.delivery_date is None:
        delivery.delivery_date = timezone.now().date()
        changed = True

    # Optional: propagate rider/branch if you assign a final-mile rider at PickupOrder level
    # (You don't currently have a rider directly on PickupOrder; keep None unless your flow sets one later.)
    # delivery.delivered_by = None

    # Mirror some useful metadata
    if getattr(delivery, "remarks", None) != (instance.remarks or ""):
        delivery.remarks = instance.remarks or ""
        changed = True

    # Keep branch aligned (models show DeliveryOrder has branch)
    if hasattr(delivery, "branch") and delivery.branch_id != instance.branch_id:
        delivery.branch = instance.branch
        changed = True

    # Keep creator aligned for traceability (optional)
    if hasattr(delivery, "user_add") and delivery.user_add_id != instance.user_add_id:
        delivery.user_add = instance.user_add
        changed = True

    return changed


@receiver(post_save, sender=PickupOrder)
def sync_delivery_order_on_pickup_save(sender, instance: PickupOrder, created: bool, **kwargs):
    """
    Ensure there is exactly one DeliveryOrder for each PickupOrder and keep it in sync.
    - On create: create a DeliveryOrder.
    - On update: update the linked DeliveryOrder, or create if missing.
    """
    # There might be multiple due to earlier data; we keep/merge the first and drop extras.
    delivery_qs = DeliveryOrder.objects.filter(pickup_order=instance).order_by("id")

    if created:
        # Create a fresh DeliveryOrder
        delivery = DeliveryOrder(
            pickup_order=instance,
            delivery_address=_derive_delivery_address(instance),
            delivery_status=_map_delivery_status(instance.status),
            remarks=instance.remarks or "",
            branch=getattr(instance, "branch", None),
            user_add=getattr(instance, "user_add", None),
        )
        # Set delivered date if already delivered at creation time (rare)
        if delivery.delivery_status == "DELIVERED" and delivery.delivery_date is None:
            delivery.delivery_date = timezone.now().date()
        delivery.save()
        return

    # Updated
    if not delivery_qs.exists():
        # Create if somehow missing
        delivery = DeliveryOrder(
            pickup_order=instance,
            delivery_address=_derive_delivery_address(instance),
            delivery_status=_map_delivery_status(instance.status),
            remarks=instance.remarks or "",
            branch=getattr(instance, "branch", None),
            user_add=getattr(instance, "user_add", None),
        )
        if delivery.delivery_status == "DELIVERED" and delivery.delivery_date is None:
            delivery.delivery_date = timezone.now().date()
        delivery.save()
        return

    # If multiple, keep the first and delete the rest to enforce 1:1
    delivery = delivery_qs.first()
    extras = delivery_qs.exclude(pk=delivery.pk)
    if extras.exists():
        extras.delete()

    if _sync_fields_from_pickup_to_delivery(instance, delivery):
        delivery.save()


@receiver(post_delete, sender=PickupOrder)
def delete_delivery_order_on_pickup_delete(sender, instance: PickupOrder, **kwargs):
    """
    When a PickupOrder is deleted, remove its DeliveryOrder(s).
    Note: bulk deletes (queryset.delete()) do NOT call signals.
    """
    DeliveryOrder.objects.filter(pickup_order=instance).delete()
