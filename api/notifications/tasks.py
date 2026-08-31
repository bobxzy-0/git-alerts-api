import ipaddress
import json
from datetime import timedelta
from urllib.parse import urlparse

import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.utils import timezone

from findings.models import Finding, FindingOccurrence
from core.models import SystemSettings
from .models import AlertDelivery, EmailConfiguration, NotificationChannel


def _scheduled_for(finding, now):
    if finding.severity in {Finding.Severity.CRITICAL, Finding.Severity.HIGH}:
        return now
    if finding.severity == Finding.Severity.MEDIUM:
        return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)


def _template_context(finding):
    return {
        "event": "finding.detected",
        "finding_id": finding.id,
        "status": finding.lifecycle_status,
        "review_status": finding.review_status,
        "severity": finding.severity,
        "source": finding.source,
        "repository": finding.repository,
        "type": finding.type,
        "description": finding.description,
        "file": finding.file,
        "line": finding.line,
        "email": finding.email,
        "commit_hash": finding.commit_hash,
        "commit_url": finding.commit_url or "",
        "value_preview": finding.value,
        "last_seen_at": finding.last_seen_at.isoformat(),
    }


def _render_template(value, context):
    if isinstance(value, dict):
        return {key: _render_template(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [_render_template(item, context) for item in value]
    if isinstance(value, str):
        rendered = value
        for key, item in context.items():
            rendered = rendered.replace("{{" + key + "}}", "" if item is None else str(item))
        return rendered
    return value


@shared_task(ignore_result=True)
def queue_scan_alerts(scan_id):
    now = timezone.now()
    occurrences = FindingOccurrence.objects.select_related("finding", "scan").filter(
        scan_id=scan_id,
        finding__lifecycle_status__in=[Finding.LifecycleStatus.NEW, Finding.LifecycleStatus.REOPENED],
    )
    created = 0
    for occurrence in occurrences:
        channels = NotificationChannel.objects.filter(user=occurrence.scan.user, enabled=True)
        for channel in channels:
            _, was_created = AlertDelivery.objects.get_or_create(
                channel=channel,
                occurrence=occurrence,
                defaults={"finding": occurrence.finding, "scheduled_for": _scheduled_for(occurrence.finding, now)},
            )
            created += int(was_created)
    send_due_alerts.delay()
    return created


@shared_task(ignore_result=True)
def send_due_alerts():
    ids = list(AlertDelivery.objects.filter(status="PENDING", scheduled_for__lte=timezone.now()).values_list("id", flat=True)[:100])
    for delivery_id in ids:
        send_alert_delivery.delay(delivery_id)
    return len(ids)


@shared_task(ignore_result=True)
def send_alert_delivery(delivery_id):
    delivery = AlertDelivery.objects.select_related("channel", "finding").get(pk=delivery_id)
    if delivery.status == AlertDelivery.Status.SENT or not delivery.channel.enabled:
        return
    finding = delivery.finding
    payload = _template_context(finding)
    try:
        if delivery.channel.channel_type == NotificationChannel.Types.EMAIL:
            email_config = EmailConfiguration.objects.filter(user=delivery.channel.user, enabled=True).first()
            connection = None
            from_email = settings.DEFAULT_FROM_EMAIL
            if email_config:
                connection = get_connection(
                    backend="django.core.mail.backends.smtp.EmailBackend",
                    host=email_config.host,
                    port=email_config.port,
                    username=email_config.username,
                    password=email_config.get_password(),
                    use_tls=email_config.use_tls,
                    use_ssl=email_config.use_ssl,
                )
                from_email = email_config.from_email
            send_mail(
                f"[{finding.severity}] {SystemSettings.get_settings().brand_name}: {finding.type}",
                "\n".join(f"{key}: {value}" for key, value in payload.items()),
                from_email,
                [delivery.channel.target],
                connection=connection,
            )
        else:
            if delivery.channel.body_template:
                template = json.loads(delivery.channel.body_template)
                request_body = _render_template(template, payload)
            else:
                request_body = payload
            requests.post(delivery.channel.target, json=request_body, timeout=(5, 15)).raise_for_status()
        delivery.status = AlertDelivery.Status.SENT
        delivery.sent_at = timezone.now()
        delivery.last_error = ""
    except Exception as exc:
        delivery.status = AlertDelivery.Status.FAILED
        delivery.last_error = str(exc)[:2000]
    delivery.attempts += 1
    delivery.save(update_fields=["status", "sent_at", "last_error", "attempts"])


def validate_webhook_target(value):
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Webhook URL must use HTTPS")
    try:
        address = ipaddress.ip_address(parsed.hostname)
        if address.is_private or address.is_loopback or address.is_link_local:
            raise ValueError("Private or local webhook targets are not allowed")
    except ValueError as exc:
        if "does not appear to be" not in str(exc):
            raise
