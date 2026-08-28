from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from core.services.scan_orchestrator import ScanOrchestrator
from findings.models import Finding
from scans.models import Scan
from .models import AlertDelivery, EmailConfiguration, NotificationChannel
from .tasks import queue_scan_alerts, send_alert_delivery, validate_webhook_target


@pytest.fixture
def finding_and_channel(db):
    user = User.objects.create_user(username="notify-user", password="test-password")
    scan = Scan.objects.create(user=user, type="org_repos", value="example")
    data = {"repository":"https://github.com/example/repo","type":"Unknown Pattern","value":"long-secret-value","description":"secret","file":"a.py","line":1,"author":"A <a@example.com>","commit":"abc","verified":False}
    ScanOrchestrator(scan, Mock(), Mock()).save_findings(data["repository"], [data])
    channel = NotificationChannel.objects.create(user=user, name="Security", channel_type="email", target="security@example.com")
    return scan, Finding.objects.get(), channel


@pytest.mark.django_db
def test_queue_only_creates_one_delivery_per_occurrence(finding_and_channel):
    scan, finding, channel = finding_and_channel
    with patch("notifications.tasks.send_due_alerts.delay"):
        assert queue_scan_alerts(scan.pk) == 1
        assert queue_scan_alerts(scan.pk) == 0
    delivery = AlertDelivery.objects.get(channel=channel, finding=finding)
    assert delivery.scheduled_for > timezone.now()


@pytest.mark.django_db
def test_resolved_finding_is_not_notified(finding_and_channel):
    scan, finding, _ = finding_and_channel
    finding.lifecycle_status = Finding.LifecycleStatus.RESOLVED
    finding.save(update_fields=["lifecycle_status"])
    with patch("notifications.tasks.send_due_alerts.delay"):
        assert queue_scan_alerts(scan.pk) == 0


@pytest.mark.django_db
def test_email_delivery_records_success(finding_and_channel):
    scan, finding, channel = finding_and_channel
    occurrence = finding.occurrences.get(scan=scan)
    delivery = AlertDelivery.objects.create(channel=channel, finding=finding, occurrence=occurrence, scheduled_for=timezone.now())
    with patch("notifications.tasks.send_mail", return_value=1) as send:
        send_alert_delivery(delivery.pk)
    delivery.refresh_from_db()
    assert delivery.status == AlertDelivery.Status.SENT
    send.assert_called_once()


@pytest.mark.django_db
def test_email_configuration_password_is_encrypted_and_not_returned():
    user = User.objects.create_user(username="smtp-user", password="test-password")
    client = APIClient()
    client.force_authenticate(user)
    response = client.patch("/notifications/email-settings/", {
        "enabled": True, "host": "smtp.example.com", "port": 587,
        "username": "alerts@example.com", "password": "smtp-secret-value",
        "from_email": "alerts@example.com", "use_tls": True, "use_ssl": False,
    }, format="json")
    assert response.status_code == 200
    assert "password" not in response.json()
    assert response.json()["password_configured"] is True
    config = EmailConfiguration.objects.get(user=user)
    assert config.password_encrypted != "smtp-secret-value"
    assert config.get_password() == "smtp-secret-value"


@pytest.mark.django_db
def test_email_delivery_uses_user_smtp_configuration(finding_and_channel):
    scan, finding, channel = finding_and_channel
    config = EmailConfiguration.objects.create(
        user=scan.user, enabled=True, host="smtp.example.com", port=465,
        username="mailer", from_email="alerts@example.com", use_tls=False, use_ssl=True,
    )
    config.set_password("secret-password")
    config.save(update_fields=["password_encrypted"])
    occurrence = finding.occurrences.get(scan=scan)
    delivery = AlertDelivery.objects.create(channel=channel, finding=finding, occurrence=occurrence, scheduled_for=timezone.now())
    connection = Mock()
    with patch("notifications.tasks.get_connection", return_value=connection) as get_connection, patch("notifications.tasks.send_mail", return_value=1) as send:
        send_alert_delivery(delivery.pk)
    get_connection.assert_called_once_with(
        backend="django.core.mail.backends.smtp.EmailBackend", host="smtp.example.com",
        port=465, username="mailer", password="secret-password", use_tls=False, use_ssl=True,
    )
    assert send.call_args.args[2] == "alerts@example.com"
    assert send.call_args.kwargs["connection"] is connection


def test_webhook_rejects_private_or_insecure_targets():
    with pytest.raises(ValueError): validate_webhook_target("http://example.com/hook")
    with pytest.raises(ValueError): validate_webhook_target("https://127.0.0.1/hook")
    validate_webhook_target("https://hooks.example.com/gitalerts")
