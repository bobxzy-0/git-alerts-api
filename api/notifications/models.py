from django.contrib.auth.models import User
from django.db import models

from findings.models import Finding, FindingOccurrence


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
