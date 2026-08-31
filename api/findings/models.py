from django.db import models
from django.utils import timezone
from scans.models import Scan

class Finding(models.Model):
    """Finding model for showing scan results"""
    class LifecycleStatus(models.TextChoices):
        NEW = "NEW", "New"
        ACTIVE = "ACTIVE", "Active"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
        RESOLVED = "RESOLVED", "Resolved"
        REOPENED = "REOPENED", "Reopened"
        IGNORED = "IGNORED", "Ignored"
        FALSE_POSITIVE = "FALSE_POSITIVE", "False Positive"

    class ReviewStatus(models.TextChoices):
        OPEN = "OPEN", "Pending review"
        CONFIRMED = "CONFIRMED", "Confirmed issue"
        FALSE_POSITIVE = "FALSE_POSITIVE", "False positive"
        IGNORED = "IGNORED", "Ignored"
        RESOLVED = "RESOLVED", "Resolved"

    class Severity(models.TextChoices):
        CRITICAL = "CRITICAL", "Critical"
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"
        INFO = "INFO", "Info"

    scan = models.ForeignKey(Scan, on_delete=models.SET_NULL, null=True, related_name="findings")
    last_scan = models.ForeignKey(Scan, on_delete=models.SET_NULL, null=True, blank=True, related_name="latest_findings")
    source = models.CharField(max_length=32, default="github")
    repository = models.CharField(max_length=512)
    type = models.CharField(max_length=512)
    value = models.TextField()
    secret_hash = models.CharField(max_length=64)
    fingerprint = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=512, blank=True)
    file = models.CharField(max_length=512)
    line = models.IntegerField(null=True, blank=True)
    email = models.CharField(max_length=255)
    commit_hash = models.CharField(max_length=255)
    commit_url = models.CharField(max_length=2048, null=True, blank=True)
    validated = models.BooleanField(default=False)
    review_status = models.CharField(max_length=24, choices=ReviewStatus.choices, default=ReviewStatus.OPEN, db_index=True)
    lifecycle_status = models.CharField(max_length=32, choices=LifecycleStatus.choices, default=LifecycleStatus.NEW)
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.MEDIUM)
    risk_score = models.PositiveSmallIntegerField(default=50)
    first_seen_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)
    occurrence_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type} - {self.value} - {self.email}"

    class Meta:
        verbose_name = "Finding"
        verbose_name_plural = "Findings"
        ordering = ["-created_at"]

class FindingOccurrence(models.Model):
    finding = models.ForeignKey(Finding, on_delete=models.CASCADE, related_name="occurrences")
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="finding_occurrences")
    observed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["finding", "scan"], name="unique_finding_occurrence_per_scan")]

class IgnoreFindingType(models.Model):
    type = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.type}"
    class Meta:
        verbose_name = "Ignored Finding Type"
        verbose_name_plural = "Ignored Finding Types"
        ordering = ["type"]

class IgnoreFindingDomain(models.Model):
    domain = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.domain}"
    class Meta:
        verbose_name = "Ignored Email Domain"
        verbose_name_plural = "Ignored Email Domains"
        ordering = ["domain"]
