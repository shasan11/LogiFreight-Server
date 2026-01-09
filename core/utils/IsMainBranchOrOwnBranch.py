from rest_framework.permissions import BasePermission

class IsMainBranchOrOwnBranch(BasePermission):
    """
    Allows access to all data if user is from the main branch.
    Otherwise, restricts access to data from user's own branch.
    """

    def has_permission(self, request, view):
        # Safe methods like GET, HEAD, OPTIONS are allowed generally
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # If user is from main branch, allow everything
        if request.user.branch and request.user.branch.is_main_branch:
            return True

        # Otherwise, restrict access to user's own branch
        return hasattr(obj, 'branch_display') and obj.branch_display == request.user.branch
