# Create your views here.
import json

from django.contrib.auth import authenticate
from django.views.generic.list import BaseListView
from django.views.generic.base import View
from django.http.response import JsonResponse

from users.models import UsersModel
from utils.jsonresponse import JsonResponseExtra


__all__ = ['UserListView', 'UsersLoginView']


class UserListView(BaseListView):
    """List users with pagination."""

    model = UsersModel
    queryset = UsersModel.objects.filter(is_delete=False)
    paginate_by = 10

    def get_paginate_by(self, queryset):
        try:
            return int(self.request.GET.get('size', 10))
        except (ValueError, TypeError):
            return 10

    def render_to_response(self, context):
        results = {'code': 200, 'msg': 'success', "data": [], 'total': 0}
        page = context.get('object_list', [])
        # Use proper model serialization
        results['data'] = [
            {
                'instance': obj.instance,
                'username': obj.username,
                'nickname': obj.nickname,
                'name': obj.name,
                'email': obj.email,
                'phone': obj.phone,
                'sex': obj.sex,
            }
            for obj in page
        ]
        if context.get('page_obj'):
            results['total'] = context['page_obj'].paginator.count
        else:
            results['total'] = self.get_queryset().count()
        return JsonResponseExtra(data=results)


class UsersLoginView(View):
    """User login view. Validates credentials against Django auth system."""

    def post(self, request):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse(
                data={'code': 400, 'msg': 'Invalid JSON body', 'data': None},
                status=400
            )

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse(
                data={'code': 400, 'msg': 'username and password are required', 'data': None},
                status=400
            )

        # Authenticate against Django's auth system
        user = authenticate(request, username=username, password=password)
        if user is None:
            return JsonResponse(
                data={'code': 401, 'msg': 'Invalid credentials', 'data': None},
                status=401
            )

        results = {
            'code': 200,
            'msg': 'success',
            'data': {
                'username': user.username,
                'id': user.pk,
            },
        }
        return JsonResponseExtra(data=results)
