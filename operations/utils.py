# operations/utils.py

READONLY_FIELDS = ("id", "created", "updated", "user_add", "history")


def stamp_user_on_create(serializer, request):
    # BranchScopedStampedOwnedActive expects user_add
    return serializer.save(user_add=request.user)
