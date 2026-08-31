from logging import getLogger
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .serializers import ExcludedRepositorySerializer, MonitorRuleSerializer, MonitoringProfileSerializer, ScanRepositorySerializer, ScanSerializer
from .models import ExcludedRepository, MonitorRule, MonitoringProfile, Scan, ScanRepository
from findings.serializers import FindingSerializer
from .tasks import dispatch_due_monitor_rules, run_monitor_rule_task, run_scan_task
from core.pagination import StandardResultsSetPagination

logger = getLogger(__name__)


class ScanView(generics.ListCreateAPIView):
    """API view for listing and creating scans"""

    serializer_class = ScanSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

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
        return Scan.objects.filter(user=self.request.user).order_by("-created_at", "-id")

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
        rule = serializer.save(user=self.request.user)
        if rule.enabled and rule.next_run_at and rule.next_run_at <= timezone.now():
            dispatch_due_monitor_rules()


class MonitorRuleDetailsView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MonitorRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MonitorRule.objects.filter(user=self.request.user)


class MonitorRuleRunNowView(generics.GenericAPIView):
    serializer_class = ScanSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        rule = get_object_or_404(MonitorRule, pk=pk, user=request.user)
        now = timezone.now()
        claimed = MonitorRule.objects.filter(pk=rule.pk, is_running=False).update(
            is_running=True, locked_at=now
        )
        if not claimed:
            return Response(
                {"detail": "This monitoring plan is already running."},
                status=status.HTTP_409_CONFLICT,
            )
        scan = Scan.objects.create(
            user=rule.user, source=rule.source, type=rule.scan_type,
            value=rule.value, trigger_type=Scan.TriggerTypes.MANUAL,
            monitor_rule=rule,
        )
        MonitorRule.objects.filter(pk=rule.pk).update(last_scan=scan)
        try:
            run_monitor_rule_task.delay(rule.pk, scan.pk, True)
        except Exception as exc:
            completed_at = timezone.now()
            scan.execution_status = Scan.ExecutionStatus.FAILED
            scan.monitoring_status = Scan.MonitoringStatus.UNKNOWN
            scan.result_status = Scan.ResultStatus.FAILED_INTERNAL
            scan.error_code = "MONITOR_DISPATCH_FAILED"
            scan.error_message = str(exc)
            scan.completed_at = completed_at
            scan.save(update_fields=[
                "execution_status", "monitoring_status", "result_status",
                "error_code", "error_message", "completed_at", "updated_at",
            ])
            MonitorRule.objects.filter(pk=rule.pk).update(
                is_running=False, locked_at=None
            )
            return Response(ScanSerializer(scan).data, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(ScanSerializer(scan).data, status=status.HTTP_202_ACCEPTED)


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
