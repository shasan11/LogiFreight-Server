from rest_framework import serializers
from django.contrib.auth.models import Group
from rest_framework.views import APIView
from rest_framework import authentication, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Group
 

class UserGroupSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField()

    def get_group_name(self, obj):
        return obj.name

    class Meta:
        model = Group
        fields = ['group_name']
 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Group
 

class UserGroupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_groups = request.user.groups.all()
        serializer = UserGroupSerializer(user_groups, many=True)
        return Response(serializer.data)
