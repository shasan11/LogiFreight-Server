from django.urls import path
from core.utils.userGroups import GetUserFirstGroupView,AssignUserToGroupView
 
urlpatterns = [
    path('users/<int:user_id>/assign-group/', AssignUserToGroupView.as_view(), name='assign-user-to-group'),
    path('users/<int:user_id>/first-group/', GetUserFirstGroupView.as_view(), name='get-user-first-group'),
]
