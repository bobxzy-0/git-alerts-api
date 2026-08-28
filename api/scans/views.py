from logging import getLogger
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .serializers import ExcludedRepositorySerializer, MonitorRuleSerializer, MonitoringProfileSerializer, ScanRepositorySerializer, ScanSerializer
from .models import ExcludedRepository, MonitorRule, MonitoringProfile, Scan, ScanRepository
from findings.serializers import FindingSerializer
from .tasks import run_scan_task

logger = getLogger(__name__)


class ScanView(generics.ListCreateAPIView):
    """API view for listing and creating scans"""

    serializer_class = ScanSerializer
    permission_classes = [IsAuthenticated]

    filterset_fields = [
        "type", "value", "execution_status", "monitoring_status",
        "result_status", "created_at", "completed_at",
        "trigger_type", "monitor_rule",
    ]
    search_fields = ["value", "type"]
    ordering_fields = [
        "created_at", "completed_at", "type", "execution_status",
        "monitoring_status", "result_status",
    ]

    def get_queryset(self):
        """Return scans created by the user"""
        return Scan.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Attach the logged-in user automatically"""
        scan = serializer.save(user=self.request.user)
        run_scan_task.delay(scan.id)
        logger.info(
            f"scan_created user={self.request.user.username} scan_id={scan.id} type={scan.type}"
        )


class ScanDetailsView(generics.RetrieveDestroyAPIView):
    """API view for retrieving and deleting individual scans"""

    serializer_class = ScanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Returns scans created by the user"""
        return Scan.objects.filter(user=self.request.user)


class ScanFindingsView(generics.ListAPIView):
    """API view for checking findings based on a scan"""

    serializer_class = FindingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Returns findings related to scan created by the user"""
        scan = get_object_or_404(
            Scan,
            pk=self.kwargs["pk"],
            user=self.request.user,
        )
        return Finding.objects.filter(occurrences__scan=scan).distinct()


class MonitorRuleView(generics.ListCreateAPIView):
    serializer_class = MonitorRuleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["enabled", "source", "scan_type", "interval_minutes"]

    def get_queryset(self):
        return MonitorRule.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MonitorRuleDetailsView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MonitorRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MonitorRule.objects.filter(user=self.request.user)


class MonitoringProfileView(generics.ListCreateAPIView):
    serializer_class = MonitoringProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MonitoringProfile.objects.filter(user=self.request.user)


class MonitoringProfileDetailsView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MonitoringProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MonitoringProfile.objects.filter(user=self.request.user)


class ScanRepositoryView(generics.ListAPIView):
    serializer_class = ScanRepositorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        scan = get_object_or_404(Scan, pk=self.kwargs["pk"], user=self.request.user)
        return ScanRepository.objects.filter(scan=scan).select_related("scan", "excluded_repository")


class ExcludedRepositoryView(generics.ListCreateAPIView):
    serializer_class = ExcludedRepositorySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["source", "enabled"]
    search_fields = ["repository_url", "owner", "repository", "reason"]

    def get_queryset(self):
        return ExcludedRepository.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExcludedRepositoryDetailsView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExcludedRepositorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExcludedRepository.objects.filter(user=self.request.user)
