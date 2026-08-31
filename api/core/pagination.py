from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Pagination used by the potentially large scan and finding lists."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
