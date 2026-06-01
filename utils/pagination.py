from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """自定义分页，匹配原有 API 响应格式。"""

    page_size = 10
    page_size_query_param = "size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "code": data.get("code", 200) if isinstance(data, dict) else 200,
            "msg": data.get("msg", "success") if isinstance(data, dict) else "success",
            "data": data.get("data", data) if isinstance(data, dict) else data,
            "total": self.page.paginator.count,
            "page": self.page.number,
            "size": self.page.paginator.per_page,
        })
