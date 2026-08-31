from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Finding


class FindingBulkDeleteView(APIView):
    """Delete many findings in database-side batches instead of N HTTP requests."""

    permission_classes = [IsAuthenticated]
    max_ids = 20000
    chunk_size = 1000

    def post(self, request):
        ids = request.data.get("ids")
        if not isinstance(ids, list):
            return Response({"detail": "ids must be an array"}, status=status.HTTP_400_BAD_REQUEST)
        if len(ids) > self.max_ids:
            return Response(
                {"detail": f"A maximum of {self.max_ids} findings can be deleted per request."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            ids = list({int(value) for value in ids})
        except (TypeError, ValueError):
            return Response({"detail": "ids must contain integers"}, status=status.HTTP_400_BAD_REQUEST)
        if not ids:
            return Response({"deleted": 0})

        deleted = 0
        for start in range(0, len(ids), self.chunk_size):
            chunk = ids[start : start + self.chunk_size]
            queryset = Finding.objects.filter(
                id__in=chunk,
                occurrences__scan__user=request.user,
            ).distinct()
            deleted += queryset.count()
            queryset.delete()
        return Response({"deleted": deleted})
