from django.core.exceptions import FieldDoesNotExist
from django.http import JsonResponse


class SystemGeneratedWriteProtectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method not in {"PUT", "PATCH", "DELETE"}:
            return None

        view_class = getattr(view_func, "view_class", None)
        if view_class is None:
            return None

        queryset = getattr(view_class, "queryset", None)
        model = getattr(queryset, "model", None)
        if model is None:
            return None

        try:
            model._meta.get_field("is_system_generated")
        except FieldDoesNotExist:
            return None

        lookup_field = getattr(view_class, "lookup_field", "pk")
        lookup_kwarg = getattr(view_class, "lookup_url_kwarg", None) or lookup_field
        lookup_value = view_kwargs.get(lookup_kwarg)
        if lookup_value is None:
            return None

        if model.objects.filter(**{lookup_field: lookup_value, "is_system_generated": True}).exists():
            return JsonResponse(
                {"detail": "System-generated records cannot be updated or deleted."},
                status=403,
            )

        return None
