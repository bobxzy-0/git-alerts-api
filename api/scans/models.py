from django.contrib.auth.models import User
from django.db import models

class Scan(models.Model):
    """Scan model for user initiated scans"""

    class ScanTypes(models.TextChoices):
        ORG_REPOS = "org_repos", "Organization Repositories"
        ORG_USERS = "org_users", "Organization Users"
        SEARCH_CODE = "search_code", "Search Code"
        SEARCH_COMMITS = "search_commits", "Search Commits"
        SEARCH_ISSUES = "search_issues", "Search Issues"
        SEARCH_REPOS = "search_repos", "Search Repositories"
        SEARCH_USERS = "search_users", "Search Users"

    class ExecutionStatus(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Success"
        DEGRADED = "DEGRADED", "Degraded"
        FAILED = "FAILED", "Failed"

    class MonitoringStatus(models.TextChoices):
        HEALTHY = "HEALTHY", "Healthy"
        WARNING = "WARNING", "Warning"
        CRITICAL = "CRITICAL", "Critical"
        UNKNOWN = "UNKNOWN", "Unknown"

    class ResultStatus(models.TextChoices):
        HEALTHY_NO_FINDINGS = "HEALTHY_NO_FINDINGS", "Healthy - No Findings"
        HEALTHY_TARGET_ABSENT = "HEALTHY_TARGET_ABSENT", "Healthy - Target Absent"
        FINDINGS_LOW = "FINDINGS_LOW", "Low Risk Findings"
        FINDINGS_MEDIUM = "FINDINGS_MEDIUM", "Medium Risk Findings"
        FINDINGS_HIGH = "FINDINGS_HIGH", "High Risk Findings"
        FINDINGS_CRITICAL = "FINDINGS_CRITICAL", "Critical Risk Findings"
        DEGRADED_RATE_LIMIT = "DEGRADED_RATE_LIMIT", "Degraded - Rate Limited"
        FAILED_AUTH = "FAILED_AUTH", "Failed - Authentication"
        FAILED_NETWORK = "FAILED_NETWORK", "Failed - Network"
        FAILED_INTERNAL = "FAILED_INTERNAL", "Failed - Internal"
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scans")
    type = models.CharField(max_length=255,choices=ScanTypes.choices, default=ScanTypes.ORG_REPOS)
    value = models.CharField(max_length=255)
    execution_status = models.CharField(
        max_length=32,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.QUEUED,
    )
    monitoring_status = models.CharField(
        max_length=32,
        choices=MonitoringStatus.choices,
        default=MonitoringStatus.UNKNOWN,
    )
    result_status = models.CharField(
        max_length=32,
        choices=ResultStatus.choices,
        null=True,
        blank=True,
    )
    error_code = models.CharField(max_length=64, blank=True, default="")
    error_message = models.TextField(blank=True, default="")

    total_repositories = models.IntegerField(default=0)
    total_findings = models.IntegerField(default=0)

    ignored_repositories = models.IntegerField(default=0)
    ignored_findings = models.IntegerField(default=0)

    scanned_repositories = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.value} - {self.execution_status}"
    
    class Meta:
        verbose_name = "Scan"
        verbose_name_plural = "Scans"
        ordering = ["-created_at"]

