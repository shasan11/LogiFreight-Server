from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()


class AssignUserToGroupView(APIView):
    """
    Assign a user to a single group (replaces old group).
    """

    def post(self, request, user_id):
        group_id = request.data.get("group_id")
        if not group_id:
            return Response({"error": "group_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            group = Group.objects.get(pk=group_id)
        except Group.DoesNotExist:
            return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

        # Replace old groups → user only has one group at a time
        user.groups.clear()
        user.groups.add(group)

        return Response(
            {"success": f"User {user.username} assigned to group {group.name}"},
            status=status.HTTP_200_OK,
        )


class GetUserFirstGroupView(APIView):
    """
    Get the first group assigned to a user.
    """

    def get(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        first_group = user.groups.first()
        if not first_group:
            return Response({"group": None}, status=status.HTTP_200_OK)

        return Response(
            {"id": first_group.id, "name": first_group.name},
            status=status.HTTP_200_OK,
        )
