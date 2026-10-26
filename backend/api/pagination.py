from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """标准分页：page size 可通过 query 参数覆盖，上限 50。"""
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 50
