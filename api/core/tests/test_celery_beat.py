from pathlib import Path

import yaml
from django.conf import settings

from core.tasks import celery_beat_heartbeat


def test_heartbeat_is_registered_in_beat_schedule():
    entry = settings.CELERY_BEAT_SCHEDULE["celery-beat-heartbeat"]
    assert entry["task"] == celery_beat_heartbeat.name
    assert entry["schedule"] == 60.0

    dispatcher = settings.CELERY_BEAT_SCHEDULE["dispatch-due-monitor-rules"]
    assert dispatcher["task"] == "scans.tasks.dispatch_due_monitor_rules"
    assert dispatcher["schedule"] == 15.0


def test_compose_defines_celery_beat_service():
    compose_path = Path(__file__).resolve().parents[3] / "docker-compose.yml"
    compose = yaml.safe_load(compose_path.read_text())
    service = compose["services"]["celery-beat"]

    assert "celery -A api beat" in service["command"]
    assert service["environment"]["CELERY_BROKER_URL"] == "redis://redis:6379/0"
    assert "celery_beat_data:/var/lib/celery" in service["volumes"]
    assert service["restart"] == "unless-stopped"
