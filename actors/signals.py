from django.db.models.signals import post_save, post_delete
from actors.models import BookingAgency, Carrier, CustomsAgent, Vendor, Customer, Department, Designation, Employee, CustomerPerson, CustomerCompany
from actors.models import MainActor
from actors.utils import upsert_main_actor, delete_main_actor, refresh_customer_main_actor_display


ACTOR_SIGNAL_MAP = [
    (BookingAgency, "booking_agency", MainActor.ActorType.BOOKING_AGENCY),
    (Carrier, "carrier", MainActor.ActorType.CARRIER),
    (CustomsAgent, "customs_agent", MainActor.ActorType.CUSTOMS_AGENT),
    (Vendor, "vendor", MainActor.ActorType.VENDOR),
    (Customer, "customer", MainActor.ActorType.CUSTOMER),
    (Department, "department", MainActor.ActorType.DEPARTMENT),
    (Designation, "designation", MainActor.ActorType.DESIGNATION),
    (Employee, "employee", MainActor.ActorType.EMPLOYEE),
]


def register_main_actor_signals():
    for model, field_name, actor_type in ACTOR_SIGNAL_MAP:

        def _post_save(sender, instance, **kwargs):
            upsert_main_actor(instance, field_name=field_name, actor_type=actor_type)

        def _post_delete(sender, instance, **kwargs):
            delete_main_actor(instance, field_name=field_name)

        post_save.connect(_post_save, sender=model, dispatch_uid=f"mainactor_postsave_{model.__name__}")
        post_delete.connect(_post_delete, sender=model, dispatch_uid=f"mainactor_postdelete_{model.__name__}")

    def _customer_person_company_save(sender, instance, **kwargs):
        refresh_customer_main_actor_display(instance.customer)

    def _customer_person_company_delete(sender, instance, **kwargs):
        refresh_customer_main_actor_display(instance.customer)

    post_save.connect(_customer_person_company_save, sender=CustomerPerson, dispatch_uid="customerperson_refresh_mainactor")
    post_save.connect(_customer_person_company_save, sender=CustomerCompany, dispatch_uid="customercompany_refresh_mainactor")
    post_delete.connect(_customer_person_company_delete, sender=CustomerPerson, dispatch_uid="customerperson_refresh_mainactor_del")
    post_delete.connect(_customer_person_company_delete, sender=CustomerCompany, dispatch_uid="customercompany_refresh_mainactor_del")
