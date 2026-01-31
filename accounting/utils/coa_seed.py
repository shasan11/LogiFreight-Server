# accounting/utils/coa_code.py

from django.core.exceptions import ValidationError
from django.db import transaction

def _assert_parent_type(instance):
    # Optional but recommended: child type must match parent type
    if instance.parent_account_id:
        parent = instance.__class__.objects.only("id", "type").get(pk=instance.parent_account_id)
        if parent.type != instance.type:
            raise ValidationError({"type": "Child account type must match parent account type."})

def _type_root_base(acc_type: str) -> int:
    roots = {
        "asset": 1000,
        "liability": 2000,
        "equity": 3000,
        "income": 4000,
        "expense": 6000,  # change to 5000 if you want expense under 5xxx
    }
    if acc_type not in roots:
        raise ValidationError({"type": f"Invalid account type: {acc_type}"})
    return roots[acc_type]

def _next_root_code(instance) -> str:
    base = _type_root_base(instance.type)

    qs = instance.__class__.objects.filter(
        branch=instance.branch,
        type=instance.type,
        parent_account__isnull=True,
    ).exclude(pk=instance.pk)

    codes = []
    for c in qs.values_list("code", flat=True):
        if c and str(c).isdigit():
            codes.append(int(c))

    if not codes:
        return str(base)

    mx = max(codes)
    nxt = (mx // 100) * 100 + 100
    if nxt < base:
        nxt = base
    return str(nxt)

def _next_child_code(instance, parent) -> str:
    if not parent.code or not str(parent.code).isdigit():
        raise ValidationError({"parent_account": "Parent code must be numeric for auto-generation."})

    p = int(parent.code)

    qs = instance.__class__.objects.filter(
        branch=instance.branch,
        parent_account=parent,
    ).exclude(pk=instance.pk)

    codes = []
    for c in qs.values_list("code", flat=True):
        if c and str(c).isdigit():
            codes.append(int(c))

    if not codes:
        return str(p + 10)

    return str(max(codes) + 10)

def generate_coa_code(instance) -> str:
    """
    Generate a code based on:
    - root per type (1000, 1100, 1200...)
    - children under parent (+10 steps: 1110, 1120...)
    Requires instance.branch and instance.type.
    """
    if not instance.branch_id:
        raise ValidationError({"branch": "Branch must be set before generating COA code."})

    _assert_parent_type(instance)

    if instance.parent_account_id:
        parent = instance.__class__.objects.only("id", "code", "type").get(pk=instance.parent_account_id)
        return _next_child_code(instance, parent)

    return _next_root_code(instance)

def lock_bucket_for_code_generation(instance):
    """
    Concurrency lock: lock the 'bucket' of siblings so two requests don't generate the same code.
    Call this inside transaction.atomic().
    """
    Model = instance.__class__

    if instance.parent_account_id:
        Model.objects.select_for_update().filter(
            branch=instance.branch,
            parent_account_id=instance.parent_account_id,
        )
    else:
        Model.objects.select_for_update().filter(
            branch=instance.branch,
            type=instance.type,
            parent_account__isnull=True,
        )
