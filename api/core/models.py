from django.db import models
from django.contrib.auth.models import User
from scans.models import Scan

class RepoScanHistory(models.Model):
    """Tracks scan history for each repository"""

    class ScanStatus(models.TextChoices):
        STARTED = "started", "Started"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped"

    repository = models.CharField(max_length=512)
    status = models.CharField(max_length=255, choices=ScanStatus.choices, default=ScanStatus.COMPLETED)
    findings_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.repository} - {self.status}"

    class Meta:
        verbose_name = "Repository"
        verbose_name_plural = "Repositories"
        ordering = ["-completed_at"]

class SystemSettings(models.Model):
    """System wide scanning configuration"""

    brand_name = models.CharField(max_length=120, default="万联源码泄漏监控")
    login_title = models.CharField(max_length=160, default="登录万联源码泄漏监控")
    home_title = models.CharField(max_length=160, default="万联源码泄漏监控")
    home_description = models.CharField(
        max_length=500,
        default="持续监控公开代码平台，发现源码与敏感信息泄漏风险",
    )

    skip_recent_days = models.IntegerField(
        default=15,
        help_text="Skip repository scanned within this many days"
    )

    verified_only = models.BooleanField(
        default=True,
        help_text="Only scan for verified secrets (faster, fewer false positives)"
    )

    org_repos_only = models.BooleanField(
        default=False,
        help_text="Only scan repositories owned by organizations (not individual users)"
    )

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "System Settings"
    
    class Meta:
        verbose_name = "System Settings",
        verbose_name_plural = "System Settings"

    @classmethod
    def get_settings(cls):
        """Get or create settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of instance"""
        pass


class SourceHealth(models.Model):
    class Status(models.TextChoices):
        HEALTHY = "HEALTHY", "Healthy"
        WARNING = "WARNING", "Warning"
        CRITICAL = "CRITICAL", "Critical"
        UNKNOWN = "UNKNOWN", "Unknown"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="source_health")
    source = models.CharField(max_length=32)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.UNKNOWN)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_failure_at = models.DateTimeField(null=True, blank=True)
    result_count = models.PositiveIntegerField(default=0)
    new_findings = models.PositiveIntegerField(default=0)
    rate_limit_remaining = models.IntegerField(null=True, blank=True)
    error_code = models.CharField(max_length=64, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["source"]
        constraints = [
            models.UniqueConstraint(fields=["user", "source"], name="unique_source_health_per_user")
        ]


class DetectionPattern(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="detection_patterns")
    name = models.CharField(max_length=255)
    finding_type = models.CharField(max_length=255)
    pattern = models.CharField(max_length=1000)
    ignore_case = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["user", "name"], name="unique_detection_pattern_name_per_user")]


class CodeFingerprint(models.Model):
    class Kind(models.TextChoices):
        BASELINE = "BASELINE", "Internal baseline"
        CANDIDATE = "CANDIDATE", "Discovered candidate"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="code_fingerprints")
    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.BASELINE)
    source_repository = models.URLField(max_length=1000, blank=True, default="")
    file_path = models.CharField(max_length=1000, blank=True, default="")
    content_sha256 = models.CharField(max_length=64, db_index=True)
    token_count = models.PositiveIntegerField(default=0)
    simhash = models.CharField(max_length=16)
    minhash = models.JSONField(default=list)
    tlsh = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class SimilarityMatch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="similarity_matches")
    baseline = models.ForeignKey(CodeFingerprint, on_delete=models.CASCADE, related_name="baseline_matches")
    candidate = models.ForeignKey(CodeFingerprint, on_delete=models.CASCADE, related_name="candidate_matches")
    simhash_score = models.FloatField()
    minhash_score = models.FloatField()
    combined_score = models.FloatField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-combined_score"]
        constraints = [models.UniqueConstraint(fields=["baseline", "candidate"], name="unique_code_similarity_pair")]
