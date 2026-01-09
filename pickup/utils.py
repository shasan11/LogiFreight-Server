# courier/utils.py
READONLY_FIELDS = ("id", "created", "updated", "user_add", "history")

def stamp_user_add(serializer, request): return serializer.save(user_add=request.user)
