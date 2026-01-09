# roles/urls.py
from django.urls import path, include
from rest_framework_bulk.routes import BulkRouter
from .views import PermissionViewSet, RoleViewSet

router = BulkRouter()
router.register(r"permissions", PermissionViewSet, basename="permission")
router.register(r"roles", RoleViewSet, basename="role")

urlpatterns = [
    path("", include(router.urls)),
]
