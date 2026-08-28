from datetime import time, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from scans.models import MonitorRule, Scan, SourceType
from scans.tasks import dispatch_due_monitor_rules, run_monitor_rule_task


@pytest.fixture
def user(db):
    return User.objects.create_user(username="rule-user", password="test-password")


@pytest.fixture
def due_rule(user):
    return MonitorRule.objects.create(
        user=user,
        name="GitHub organization",
        source=SourceType.GITHUB,
        scan_type=Scan.ScanTypes.ORG_REPOS,
        value="example",
        interval_minutes=MonitorRule.Intervals.MINUTES_15,
        next_run_at=timezone.now() - timedelta(minutes=1),
    )


@pytest.mark.django_db
def test_rule_supports_required_intervals():
    assert {choice.value for choice in MonitorRule.Intervals} == {
        15, 30, 60, 120, 360, 720, 1440,
    }


@pytest.mark.django_db
def test_daily_rule_calculates_next_requested_time(user):
    rule = MonitorRule.objects.create(
        user=user,
        name="Daily",
        scan_type=Scan.ScanTypes.SEARCH_REPOS,
        value="company",
        schedule_kind=MonitorRule.ScheduleKinds.DAILY,
        schedule_time=time(9, 30),
    )
    local_next = timezone.localtime(rule.next_run_at)
    assert (local_next.hour, local_next.minute) == (9, 30)


@pytest.mark.django_db
def test_cron_rule_and_invalid_cron_api(user):
    client = APIClient()
    client.force_authenticate(user)
    payload = {
        "name": "Cron", "source": "github", "scan_type": "search_repos",
        "value": "company", "schedule_kind": "CRON",
        "cron_expression": "0 9 * * 1-5", "interval_minutes": 60,
    }
    assert client.post("/monitor-rules/", payload, format="json").status_code == 201
    payload["name"] = "Bad cron"
    payload["cron_expression"] = "not a cron"
    assert client.post("/monitor-rules/", payload, format="json").status_code == 400


@pytest.mark.django_db
def test_new_enabled_rule_is_due_immediately(user):
    before = timezone.now()
    rule = MonitorRule.objects.create(
        user=user,
        name="Immediate",
        scan_type=Scan.ScanTypes.SEARCH_REPOS,
        value="company-name",
    )
    assert rule.next_run_at >= before


@pytest.mark.django_db
def test_dispatch_claims_same_rule_only_once(due_rule):
    with patch("scans.tasks.run_monitor_rule_task.delay") as delay:
        assert dispatch_due_monitor_rules() == 1
        assert dispatch_due_monitor_rules() == 0

    scan = Scan.objects.get(user=due_rule.user, value=due_rule.value)
    delay.assert_called_once_with(due_rule.pk, scan.pk)
    due_rule.refresh_from_db()
    assert due_rule.is_running is True
    assert due_rule.locked_at is not None
    assert due_rule.last_scan_id == scan.pk
    assert scan.trigger_type == Scan.TriggerTypes.SCHEDULED
    assert scan.monitor_rule_id == due_rule.pk


@pytest.mark.django_db
def test_dispatch_failure_leaves_failed_scan_and_releases_rule(due_rule):
    with patch("scans.tasks.run_monitor_rule_task.delay", side_effect=RuntimeError("broker down")):
        assert dispatch_due_monitor_rules() == 0

    scan = Scan.objects.get(user=due_rule.user, value=due_rule.value)
    due_rule.refresh_from_db()
    assert scan.execution_status == Scan.ExecutionStatus.FAILED
    assert scan.result_status == Scan.ResultStatus.FAILED_INTERNAL
    assert scan.error_code == "MONITOR_DISPATCH_FAILED"
    assert due_rule.is_running is False
    assert due_rule.last_scan_id == scan.pk


@pytest.mark.django_db
def test_dispatch_recovers_legacy_lock_without_scan(due_rule):
    MonitorRule.objects.filter(pk=due_rule.pk).update(
        is_running=True,
        locked_at=timezone.now() - timedelta(minutes=6),
        last_scan=None,
    )
    with patch("scans.tasks.run_monitor_rule_task.delay") as delay:
        assert dispatch_due_monitor_rules() == 1

    scan = Scan.objects.get(user=due_rule.user, value=due_rule.value)
    delay.assert_called_once_with(due_rule.pk, scan.pk)


@pytest.mark.django_db
def test_rule_execution_creates_scan_and_releases_lock(due_rule):
    MonitorRule.objects.filter(pk=due_rule.pk).update(is_running=True, locked_at=timezone.now())
    with patch("scans.tasks.run_scan_task") as run_scan:
        scan_id = run_monitor_rule_task(due_rule.pk)

    scan = Scan.objects.get(pk=scan_id)
    run_scan.assert_called_once_with(scan.pk)
    due_rule.refresh_from_db()
    assert due_rule.is_running is False
    assert due_rule.locked_at is None
    assert due_rule.last_scan_id == scan.pk
    assert due_rule.last_run_at is not None
    assert due_rule.next_run_at >= due_rule.last_run_at + timedelta(minutes=15)


@pytest.mark.django_db
def test_run_now_creates_manual_scan_without_moving_schedule(user, due_rule):
    client = APIClient()
    client.force_authenticate(user)
    original_next_run = due_rule.next_run_at
    with patch("scans.views.run_monitor_rule_task.delay") as delay:
        response = client.post(f"/monitor-rules/{due_rule.pk}/run/")

    assert response.status_code == 202
    scan = Scan.objects.get(pk=response.json()["id"])
    assert scan.trigger_type == Scan.TriggerTypes.MANUAL
    assert scan.monitor_rule_id == due_rule.pk
    delay.assert_called_once_with(due_rule.pk, scan.pk, True)
    due_rule.refresh_from_db()
    assert due_rule.next_run_at == original_next_run


@pytest.mark.django_db
def test_run_now_rejects_concurrent_rule(user, due_rule):
    MonitorRule.objects.filter(pk=due_rule.pk).update(is_running=True)
    client = APIClient()
    client.force_authenticate(user)
    assert client.post(f"/monitor-rules/{due_rule.pk}/run/").status_code == 409


@pytest.mark.django_db
def test_monitor_rule_api_is_user_scoped(user):
    other = User.objects.create_user(username="other-user", password="test-password")
    MonitorRule.objects.create(
        user=other,
        name="Other rule",
        scan_type=Scan.ScanTypes.ORG_REPOS,
        value="other",
    )
    client = APIClient()
    client.force_authenticate(user)
    response = client.post(
        "/monitor-rules/",
        {
            "name": "My rule",
            "source": "github",
            "scan_type": "org_repos",
            "value": "example",
            "interval_minutes": 30,
            "enabled": True,
        },
        format="json",
    )
    assert response.status_code == 201
    assert client.get("/monitor-rules/").json()[0]["name"] == "My rule"


@pytest.mark.django_db
def test_gitlab_source_is_enabled(user):
    client = APIClient()
    client.force_authenticate(user)
    response = client.post(
        "/monitor-rules/",
        {
            "name": "GitLab group",
            "source": "gitlab",
            "scan_type": "org_repos",
            "value": "example",
            "interval_minutes": 60,
        },
        format="json",
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_gitee_source_is_enabled(user):
    client = APIClient()
    client.force_authenticate(user)
    response = client.post("/monitor-rules/", {
        "name": "Gitee org", "source": "gitee", "scan_type": "org_repos",
        "value": "example", "interval_minutes": 60,
    }, format="json")
    assert response.status_code == 201
