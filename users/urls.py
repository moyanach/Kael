from django.urls import path

from users.views import UserListView, UsersLoginView

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('login/', UsersLoginView.as_view(), name='user-login'),
]
