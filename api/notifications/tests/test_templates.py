from django.contrib.auth.models import User
from django.test import TestCase

from findings.models import Finding
from notifications.models import NotificationChannel
from notifications.serializers import NotificationChannelSerializer
from scans.models import Scan


class NotificationTemplateTests(TestCase):
    def test_webhook_template_accepts_json(self):
        user = User.objects.create_user(username="notify-user", password="test")
        serializer = NotificationChannelSerializer(data={
            "name": "DingTalk",
            "channel_type": NotificationChannel.Types.WEBHOOK,
            "target": "https://example.com/hooks/security",
            "body_template": '{"msgtype":"text","text":{"content":"{{severity}} {{repository}}"}}',
            "enabled": True,
        }, context={"request": type("Request", (), {"user": user})()})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_webhook_template_rejects_invalid_json(self):
        user = User.objects.create_user(username="notify-user-2", password="test")
        serializer = NotificationChannelSerializer(data={
            "name": "Webhook",
            "channel_type": NotificationChannel.Types.WEBHOOK,
            "target": "https://example.com/hooks/security",
            "body_template": "not-json",
            "enabled": True,
        }, context={"request": type("Request", (), {"user": user})()})
        self.assertFalse(serializer.is_valid())
        self.assertIn("body_template", serializer.errors)
