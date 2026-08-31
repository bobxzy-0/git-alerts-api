from logging import getLogger
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .serializers import FindingSerializer, IgnoreFindingTypeSerializer, IgnoreFindingDomainSerializer
from .models import Finding, IgnoreFindingType, IgnoreFindingDomain
from core.pagination import StandardResultsSetPagination

logger = getLogger(__name__)

class FindingView(generics.ListAPIView):
    serializer_class = FindingSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_fields = ["type", "email", "repository", "validated", "review_status", "lifecycle_status", "severity", "source", "created_at"]
    search_fields = ["repository", "email", "description", "value", "commit_hash"]
    ordering_fields = ["created_at", "type", "repository", "email"]
    def get_queryset(self):
        queryset = Finding.objects.filter(occurrences__scan__user=self.request.user).distinct().order_by("-created_at", "-id")
        scan_id = self.request.query_params.get("scan")
        if scan_id: queryset = queryset.filter(occurrences__scan_id=scan_id)
        return queryset

class FindingDetailsView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FindingSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self): return Finding.objects.filter(occurrences__scan__user=self.request.user).distinct()

class IgnoreFindingTypeView(generics.ListCreateAPIView):
    queryset = IgnoreFindingType.objects.all(); serializer_class = IgnoreFindingTypeSerializer; permission_classes = [IsAuthenticated]

class IgnoreFindingTypeDetailsView(generics.RetrieveDestroyAPIView):
    serializer_class = IgnoreFindingTypeSerializer; permission_classes = [IsAuthenticated]
    def get_queryset(self): return IgnoreFindingType.objects.filter(id=self.kwargs["pk"])

class IgnoreFindingDomainView(generics.ListCreateAPIView):
    queryset = IgnoreFindingDomain.objects.all(); serializer_class = IgnoreFindingDomainSerializer; permission_classes = [IsAuthenticated]

class IgnoredFindingDomainDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = IgnoreFindingDomainSerializer; permission_classes = [IsAuthenticated]
    def get_queryset(self): return IgnoreFindingDomain.objects.filter(id=self.kwargs["pk"])
