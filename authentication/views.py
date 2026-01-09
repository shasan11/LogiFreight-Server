# roles/views.py
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import (
    PermissionSerializer,
    RoleSerializer,
    RoleAssignUsersSerializer,
)

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List/search all permissions.
    """
    queryset = Permission.objects.select_related("content_type").all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["content_type__app_label", "content_type__model"]
    search_fields = ["name", "codename"]
    ordering_fields = ["content_type__app_label", "codename", "name"]
    ordering = ["content_type__app_label", "codename"]

class RoleViewSet(viewsets.ModelViewSet):
    """
    CRUD roles (Groups) + assign users.
    Accepts `permission_ids: [1,2,3]` on create/update.
    """
    queryset = Group.objects.prefetch_related("permissions").all()
    serializer_class = RoleSerializer
    # Use IsAdminUser for simplicity; you can switch to DjangoModelPermissions if you prefer.
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]
    ordering = ["name"]

    @action(detail=True, methods=["post"], url_path="assign-users")
    def assign_users(self, request, pk=None):
        """
        Body:
        {
          "user_ids": [3, 5, 7],
          "mode": "add" | "remove" | "set"   (default: "set")
        }
        """
        group = self.get_object()
        serializer = RoleAssignUsersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_ids = serializer.validated_data["user_ids"]
        mode = serializer.validated_data["mode"]

        User = get_user_model()
        users = list(User.objects.filter(id__in=user_ids))

        if mode == "set":
            group.user_set.set(users)
        elif mode == "add":
            for u in users:
                group.user_set.add(u)
        elif mode == "remove":
            for u in users:
                group.user_set.remove(u)

        return Response(
            {
                "id": group.id,
                "name": group.name,
                "user_count": group.user_set.count(),
            },
            status=status.HTTP_200_OK,
        )
