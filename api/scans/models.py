from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import time


class SourceType(models.TextChoices):
    GITHUB = "github", "GitHub"
    GITLAB = "gitlab", "GitLab"
    GITEE = "gitee", "Gitee"
    BITBUCKET = "bitbucket", "Bitbucket"
    CODEBERG = "codeberg", "Codeberg"
    YOU = "you", "You.com Search"

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
        REPOSITORY = "repository", "Direct Repository"

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

    class TriggerTypes(models.TextChoices):
        MANUAL = "MANUAL", "Manual"
        SCHEDULED = "SCHEDULED", "Scheduled"
        DISCOVERY = "DISCOVERY", "Discovery"
        REPOSITORY_QUEUE = "REPOSITORY_QUEUE", "Repository queue"
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scans")
    type = models.CharField(max_length=255,choices=ScanTypes.choices, default=ScanTypes.ORG_REPOS)
    value = models.CharField(max_length=255)
    source = models.CharField(max_length=32, choices=SourceType.choices, default=SourceType.GITHUB)
    trigger_type = models.CharField(max_length=32, choices=TriggerTypes.choices, default=TriggerTypes.MANUAL, db_index=True)
    monitor_rule = models.ForeignKey(
        "MonitorRule", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="scans",
    )
    execution_status = models.CharField(max_length=32, choices=ExecutionStatus.choices, default=ExecutionStatus.QUEUED)
    monitoring_status = models.CharField(max_length=32, choices=MonitoringStatus.choices, default=MonitoringStatus.UNKNOWN)
    result_status = models.CharField(max_length=32, choices=ResultStatus.choices, null=True, blank=True)
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


class MonitorRule(models.Model):
    """A recurring discovery rule dispatched by Celery Beat."""

    class Intervals(models.IntegerChoices):
        MINUTES_15 = 15, "15 minutes"
        MINUTES_30 = 30, "30 minutes"
        HOUR_1 = 60, "1 hour"
        HOURS_2 = 120, "2 hours"
        HOURS_6 = 360, "6 hours"
        HOURS_12 = 720, "12 hours"
        HOURS_24 = 1440, "24 hours"

    class ScheduleKinds(models.TextChoices):
        INTERVAL = "INTERVAL", "Fixed interval"
        DAILY = "DAILY", "Daily"
        WEEKLY = "WEEKLY", "Weekly"
        CRON = "CRON", "Cron expression"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="monitor_rules")
    profile = models.ForeignKey("MonitoringProfile", null=True, blank=True, on_delete=models.CASCADE, related_name="rules")
    auto_generated = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)
    source = models.CharField(max_length=32, choices=SourceType.choices, default=SourceType.GITHUB)
    scan_type = models.CharField(max_length=255, choices=Scan.ScanTypes.choices)
    value = models.CharField(max_length=512)
    interval_minutes = models.PositiveIntegerField(choices=Intervals.choices, default=Intervals.HOUR_1)
    schedule_kind = models.CharField(max_length=16, choices=ScheduleKinds.choices, default=ScheduleKinds.INTERVAL)
    schedule_time = models.TimeField(default=time(0, 0))
    schedule_weekdays = models.JSONField(default=list, blank=True)
    cron_expression = models.CharField(max_length=100, blank=True, default="")
    timezone = models.CharField(max_length=64, default="Asia/Shanghai")
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True, db_index=True)
    is_running = models.BooleanField(default=False, db_index=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    last_scan = models.ForeignKey(Scan, on_delete=models.SET_NULL, null=True, blank=True, related_name="monitor_rule_runs")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.enabled and self.next_run_at is None:
            self.next_run_at = self.next_occurrence(timezone.now())
        super().save(*args, **kwargs)

    def next_occurrence(self, after):
        from .services.scheduling import next_occurrence
        return next_occurrence(self, after)

    def __str__(self):
        return f"{self.name} ({self.source}: {self.value})"

    class Meta:
        ordering = ["name"]


class MonitoringProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="monitoring_profiles")
    name = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)
    company_name = models.CharField(max_length=255, blank=True, default="")
    domains = models.JSONField(default=list, blank=True)
    email_domains = models.JSONField(default=list, blank=True)
    brands = models.JSONField(default=list, blank=True)
    product_names = models.JSONField(default=list, blank=True)
    internal_projects = models.JSONField(default=list, blank=True)
    internal_domains = models.JSONField(default=list, blank=True)
    github_orgs = models.JSONField(default=list, blank=True)
    gitlab_groups = models.JSONField(default=list, blank=True)
    custom_keywords = models.JSONField(default=list, blank=True)
    interval_minutes = models.PositiveIntegerField(choices=MonitorRule.Intervals.choices, default=MonitorRule.Intervals.HOUR_1)
    schedule_kind = models.CharField(max_length=16, choices=MonitorRule.ScheduleKinds.choices, default=MonitorRule.ScheduleKinds.INTERVAL)
    schedule_time = models.TimeField(default=time(0, 0))
    schedule_weekdays = models.JSONField(default=list, blank=True)
    cron_expression = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["user", "name"], name="unique_monitoring_profile_name_per_user")]


class RepositoryScanQueue(models.Model):
    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="repository_scan_queue")
    discovery_scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="repository_queue_items")
    source = models.CharField(max_length=32, choices=SourceType.choices)
    repository_url = models.URLField(max_length=1000)
    owner = models.CharField(max_length=255)
    repository = models.CharField(max_length=255)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED, db_index=True)
    scan = models.ForeignKey(Scan, null=True, blank=True, on_delete=models.SET_NULL, related_name="queue_sources")
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["discovery_scan", "source", "repository_url"], name="unique_discovered_repository_per_scan")]


class ExcludedRepository(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="excluded_repositories")
    source = models.CharField(max_length=32, choices=SourceType.choices)
    repository_url = models.URLField(max_length=1000)
    normalized_url = models.CharField(max_length=1000, db_index=True)
    owner = models.CharField(max_length=255, blank=True, default="")
    repository = models.CharField(max_length=255, blank=True, default="")
    reason = models.CharField(max_length=500, blank=True, default="")
    enabled = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        from .services.repositories import normalize_repository_url
        self.normalized_url = normalize_repository_url(self.repository_url)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["source", "owner", "repository"]
        constraints = [models.UniqueConstraint(fields=["user", "source", "normalized_url"], name="unique_excluded_repository_per_user")]


class ScanRepository(models.Model):
    class Status(models.TextChoices):
        DISCOVERED = "DISCOVERED", "Discovered"
        EXCLUDED = "EXCLUDED", "Permanently excluded"
        SKIPPED_RECENT = "SKIPPED_RECENT", "Recently scanned"
        QUEUED = "QUEUED", "Queued"
        SCANNING = "SCANNING", "Scanning"
        COMPLETED = "COMPLETED", "Completed"
        DEGRADED = "DEGRADED", "Partially scanned"
        FAILED = "FAILED", "Failed"

    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="repositories")
    source = models.CharField(max_length=32, choices=SourceType.choices)
    repository_url = models.URLField(max_length=1000)
    normalized_url = models.CharField(max_length=1000, db_index=True)
    owner = models.CharField(max_length=255, blank=True, default="")
    repository = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DISCOVERED, db_index=True)
    excluded_repository = models.ForeignKey(ExcludedRepository, null=True, blank=True, on_delete=models.SET_NULL, related_name="scan_records")
    error_message = models.TextField(blank=True, default="")
    findings_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["source", "owner", "repository"]
        constraints = [models.UniqueConstraint(fields=["scan", "source", "normalized_url"], name="unique_repository_per_scan")]
