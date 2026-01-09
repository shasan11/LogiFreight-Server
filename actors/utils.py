from __future__ import annotations
from typing import Optional
from actors.models import MainActor


def upsert_main_actor(instance, field_name: str, actor_type: str) -> MainActor:
    defaults = {"branch": instance.branch, "actor_type": actor_type, "display_name": str(instance)}
    obj, _ = MainActor.objects.update_or_create(**{field_name: instance}, defaults=defaults)
    return obj


def delete_main_actor(instance, field_name: str) -> None:
    MainActor.objects.filter(**{field_name: instance}).delete()


def refresh_customer_main_actor_display(customer) -> None:
    if not hasattr(customer, "main_actor"):
        return
    ma = customer.main_actor
    ma.display_name = str(customer)
    ma.save(update_fields=["display_name", "updated"])


def get_main_actor_for_instance(instance) -> Optional[MainActor]:
    rel = getattr(instance, "main_actor", None)
    if rel:
        return rel
    return None
