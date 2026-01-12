# master/utils.py

READONLY_FIELDS_CREATED_UPDATED = ("id", "created", "updated_at", "history")
READONLY_FIELDS_ID_ONLY = ("id",)

USER_STAMP_FIELDS = ("user_add", "add_by", "added_by")


def stamp_user_on_create(serializer, request):
    """
    Auto-stamps the correct user field if the model has one:
    - user_add / add_by / added_by
    """
    model = serializer.Meta.model
    model_field_names = {f.name for f in model._meta.fields}

    for field in USER_STAMP_FIELDS:
        if field in model_field_names:
            return serializer.save(**{field: request.user})

    return serializer.save()
