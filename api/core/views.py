from rest_framework import generics
from .models import CodeFingerprint, DetectionPattern, SimilarityMatch, SourceHealth, SystemSettings
from .serializers import CodeFingerprintSerializer, DetectionPatternSerializer, SimilarityMatchSerializer, SourceHealthSerializer, SystemSettingsSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from findings.models import Finding
from findings.serializers import FindingSerializer
from scans.models import Scan
from scans.serializers import ScanSerializer

class SystemSettingsView(generics.RetrieveUpdateAPIView):
    """Get or update system-wide settings"""
    serializer_class = SystemSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return SystemSettings.get_settings()


class SourceHealthView(generics.ListAPIView):
    serializer_class = SourceHealthSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SourceHealth.objects.filter(user=self.request.user)


class DetectionPatternListCreateView(generics.ListCreateAPIView):
    serializer_class = DetectionPatternSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DetectionPattern.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DetectionPatternDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DetectionPatternSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DetectionPattern.objects.filter(user=self.request.user)


class CodeFingerprintListCreateView(generics.ListCreateAPIView):
    serializer_class = CodeFingerprintSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CodeFingerprint.objects.filter(user=self.request.user)


class SimilarityMatchListView(generics.ListAPIView):
    serializer_class = SimilarityMatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SimilarityMatch.objects.filter(user=self.request.user).select_related("baseline", "candidate")


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        scans = Scan.objects.filter(user=request.user)
        findings = Finding.objects.filter(
            occurrences__scan__user=request.user
        ).distinct()
        source_health = SourceHealth.objects.filter(user=request.user)
        health_rank = {"HEALTHY": 0, "UNKNOWN": 1, "WARNING": 2, "CRITICAL": 3}
        overall_health = max(
            (item.status for item in source_health),
            key=lambda status: health_rank[status],
            default="UNKNOWN",
        )
        severity_counts = {severity: 0 for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]}
        for row in findings.values("severity").annotate(count=Count("id")):
            severity_counts[row["severity"]] = row["count"]
        trend_start = timezone.now() - timedelta(days=13)
        trend_rows = (
            scans.filter(created_at__gte=trend_start)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        trend_by_day = {row["day"]: row["count"] for row in trend_rows}
        today = timezone.localdate()
        return Response({
            "overall_health": overall_health,
            "source_health": SourceHealthSerializer(source_health, many=True).data,
            "severity_counts": severity_counts,
            "new_findings": findings.filter(
                lifecycle_status__in=["NEW", "REOPENED"]
            ).count(),
            "resolved_findings": findings.filter(lifecycle_status="RESOLVED").count(),
            "recent_scans": ScanSerializer(scans[:5], many=True).data,
            "recent_findings": FindingSerializer(findings.order_by("-last_seen_at")[:5], many=True).data,
            "scan_trend": [
                {"date": day.isoformat(), "count": trend_by_day.get(day, 0)}
                for day in (today - timedelta(days=offset) for offset in range(13, -1, -1))
            ],
        })
