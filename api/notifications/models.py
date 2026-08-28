from django.contrib.auth.models import User
from django.db import models

from findings.models import Finding, FindingOccurrence
from core.crypto import encypt, decrypt


class EmailConfiguration(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="email_configuration")
    enabled = models.BooleanField(default=False)
    host = models.CharField(max_length=255, blank=True, default="")
    port = models.PositiveIntegerField(default=587)
    username = models.CharField(max_length=255, blank=True, default="")
    password_encrypted = models.TextField(blank=True, default="")
    from_email = models.EmailField(blank=True, default="")
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, password: str) -> None:
        if password:
            self.password_encrypted = encypt(password)

    def get_password(self) -> str:
        return decrypt(self.password_encrypted) if self.password_encrypted else ""


class NotificationChannel(models.Model):
    class Types(models.TextChoices):
        EMAIL = "email", "Email"
        WEBHOOK = "webhook", "Webhook"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notification_channels")
    name = models.CharField(max_length=255)
    channel_type = models.CharField(max_length=16, choices=Types.choices)
    target = models.CharField(max_length=2048)
    secret_encrypted = models.TextField(blank=True, default="")
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "name"], name="unique_notification_channel_name")]


class AlertDelivery(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"

    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE, related_name="deliveries")
    finding = models.ForeignKey(Finding, on_delete=models.CASCADE, related_name="alert_deliveries")
    occurrence = models.ForeignKey(FindingOccurrence, on_delete=models.CASCADE, related_name="alert_deliveries")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    scheduled_for = models.DateTimeField(db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["channel", "occurrence"], name="unique_alert_per_channel_occurrence")]
