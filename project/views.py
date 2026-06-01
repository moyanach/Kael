# Create your views here.
import json

from django.views.generic.list import BaseListView
from django.views.generic.base import View
from django.http.response import JsonResponse

from project.models import ApplicationModel
from utils.jsonresponse import JsonResponseExtra


__all__ = ('ProjectView', 'ProjectCreateView')


class ProjectView(BaseListView):
    """List applications with pagination."""

    model = ApplicationModel
    queryset = ApplicationModel.objects.all()
    paginate_by = 10

    def get_paginate_by(self, queryset):
        try:
            return int(self.request.GET.get('size', 10))
        except (ValueError, TypeError):
            return 10

    def render_to_response(self, context):
        results = {'code': 200, 'msg': 'success', "data": [], 'total': 0}
        page = context.get('object_list', [])
        # Use proper model serialization instead of Django's serializer
        results['data'] = [
            {
                'instance': obj.instance,
                'name': obj.name,
                'lang': obj.lang,
                'level': obj.level,
                'mold': obj.mold,
                'cost_mode': obj.cost_mode,
                'is_docker': obj.is_docker,
                'health': obj.health,
                'handle_info': obj.handle_info,
                'description': obj.description,
                'owner_id': obj.owner_id,
                'business_id': obj.business_id,
                'product_id': obj.product_id,
                'create_user': obj.create_user,
                'create_time': str(obj.create_time) if obj.create_time else None,
                'update_time': str(obj.update_time) if obj.update_time else None,
            }
            for obj in page
        ]
        results['total'] = self.get_queryset().count()
        if context.get('page_obj'):
            results['total'] = context['page_obj'].paginator.count
        return JsonResponseExtra(data=results)


class ProjectCreateView(View):
    """Create a new application. Only allowed fields are accepted."""

    # Whitelist of fields that can be set via API (prevents mass assignment)
    ALLOWED_FIELDS = {
        'name', 'lang', 'level', 'mold', 'cost_mode',
        'is_docker', 'health', 'handle_info', 'description',
        'owner_id', 'business_id', 'product_id',
    }

    def post(self, request):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse(
                data={'code': 400, 'msg': 'Invalid JSON body', 'data': None},
                status=400
            )

        # Filter to only allowed fields (mass assignment protection)
        filtered_data = {k: v for k, v in data.items() if k in self.ALLOWED_FIELDS}

        # Require name field
        if not filtered_data.get('name'):
            return JsonResponse(
                data={'code': 400, 'msg': 'name is required', 'data': None},
                status=400
            )

        try:
            application_obj = ApplicationModel(**filtered_data)
            application_obj.full_clean()
            application_obj.save()
            results = {
                'code': 200,
                'msg': 'success',
                'data': {'instance': application_obj.instance},
            }
        except Exception as err:
            return JsonResponse(
                data={'code': 400, 'msg': str(err), 'data': None},
                status=400
            )

        return JsonResponseExtra(data=results)
