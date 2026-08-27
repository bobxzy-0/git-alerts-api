from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User

from core.models import SourceHealth
from core.sources import (
    AdapterHealth, SourceAuthError, SourceNetworkError, SourceRateLimitError,
    SourceResponseError,
)
from integrations.models import UserIntegration
from scans.models import Scan
from scans.tasks import run_scan_task


@pytest.fixture
def scan_with_integration(db):
    user = User.objects.create_user(username="scan-user", password="test-password")
    scan = Scan.objects.create(user=user, type=Scan.ScanTypes.ORG_REPOS, value="example")
    UserIntegration.objects.create(
        user=user,
        provider=UserIntegration.Provider.GITHUB,
        status=UserIntegration.Status.CONNECTED,
        token_encrypted="test-token",
    )
    return scan


def run_with_orchestrator(scan, *, repositories, findings, successes=0, failures=0):
    def orchestrator_run():
        Scan.objects.filter(pk=scan.pk).update(
            total_repositories=repositories,
            total_findings=findings,
        )

    adapter = Mock()
    adapter.health_check.return_value = AdapterHealth(True, 4999)
    with (
        patch.object(UserIntegration, "get_token", return_value="github-token"),
        patch("scans.tasks.get_source_adapter", return_value=adapter),
        patch("scans.tasks.ScanOrchestrator") as orchestrator_class,
    ):
        orchestrator = orchestrator_class.return_value
        orchestrator.repository_successes = successes
        orchestrator.repository_failures = failures
        orchestrator.run.side_effect = orchestrator_run
        run_scan_task(scan.pk)

    scan.refresh_from_db()
    return scan


@pytest.mark.django_db
def test_zero_search_results_are_healthy_not_failed(scan_with_integration):
    scan = run_with_orchestrator(scan_with_integration, repositories=0, findings=0)

    assert scan.execution_status == Scan.ExecutionStatus.SUCCESS
    assert scan.monitoring_status == Scan.MonitoringStatus.HEALTHY
    assert scan.result_status == Scan.ResultStatus.HEALTHY_TARGET_ABSENT
    health = SourceHealth.objects.get(user=scan.user, source="github")
    assert health.status == SourceHealth.Status.HEALTHY
    assert health.result_count == 0
    assert health.rate_limit_remaining == 4999


@pytest.mark.django_db
def test_zero_findings_are_healthy_not_failed(scan_with_integration):
    scan = run_with_orchestrator(
        scan_with_integration, repositories=2, findings=0, successes=2
    )

    assert scan.execution_status == Scan.ExecutionStatus.SUCCESS
    assert scan.monitoring_status == Scan.MonitoringStatus.HEALTHY
    assert scan.result_status == Scan.ResultStatus.HEALTHY_NO_FINDINGS


@pytest.mark.django_db
def test_gitlab_zero_results_are_healthy():
    user = User.objects.create_user(username="gitlab-user", password="password")
    scan = Scan.objects.create(
        user=user, source="gitlab", type=Scan.ScanTypes.ORG_REPOS, value="acme"
    )
    UserIntegration.objects.create(
        user=user, provider=UserIntegration.Provider.GITLAB,
        status=UserIntegration.Status.CONNECTED, token_encrypted="token",
    )
    adapter = Mock()
    adapter.health_check.return_value = AdapterHealth(True, None)
    with (
        patch.object(UserIntegration, "get_token", return_value="gitlab-token"),
        patch("scans.tasks.get_source_adapter", return_value=adapter) as registry,
        patch("scans.tasks.ScanOrchestrator") as orchestrator_class,
    ):
        orchestrator_class.return_value.repository_successes = 0
        orchestrator_class.return_value.repository_failures = 0
        run_scan_task(scan.pk)

    scan.refresh_from_db()
    registry.assert_called_once_with("gitlab", token="gitlab-token")
    assert scan.execution_status == Scan.ExecutionStatus.SUCCESS
    assert scan.monitoring_status == Scan.MonitoringStatus.HEALTHY
    assert scan.result_status == Scan.ResultStatus.HEALTHY_TARGET_ABSENT
    assert SourceHealth.objects.get(user=user, source="gitlab").status == SourceHealth.Status.HEALTHY


@pytest.mark.django_db
def test_findings_do_not_make_execution_fail(scan_with_integration):
    scan = run_with_orchestrator(
        scan_with_integration, repositories=1, findings=3, successes=1
    )

    assert scan.execution_status == Scan.ExecutionStatus.SUCCESS
    assert scan.monitoring_status == Scan.MonitoringStatus.WARNING
    assert scan.result_status == Scan.ResultStatus.FINDINGS_MEDIUM


@pytest.mark.django_db
def test_partial_repository_failure_is_degraded(scan_with_integration):
    scan = run_with_orchestrator(
        scan_with_integration, repositories=2, findings=0, successes=1, failures=1
    )

    assert scan.execution_status == Scan.ExecutionStatus.DEGRADED
    assert scan.monitoring_status == Scan.MonitoringStatus.WARNING
    assert scan.error_code == "REPOSITORY_SCAN_PARTIAL_FAILURE"


@pytest.mark.django_db
def test_all_repository_failures_are_internal_failure(scan_with_integration):
    scan = run_with_orchestrator(
        scan_with_integration, repositories=2, findings=0, successes=0, failures=2
    )

    assert scan.execution_status == Scan.ExecutionStatus.FAILED
    assert scan.monitoring_status == Scan.MonitoringStatus.UNKNOWN
    assert scan.result_status == Scan.ResultStatus.FAILED_INTERNAL
    assert scan.error_code == "REPOSITORY_SCAN_FAILED"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("exception", "execution", "monitoring", "result"),
    [
        (SourceAuthError("bad token"), "FAILED", "UNKNOWN", "FAILED_AUTH"),
        (SourceNetworkError("network down"), "FAILED", "UNKNOWN", "FAILED_NETWORK"),
        (SourceRateLimitError("limited"), "DEGRADED", "WARNING", "DEGRADED_RATE_LIMIT"),
        (SourceResponseError("bad json"), "FAILED", "UNKNOWN", "FAILED_INTERNAL"),
        (RuntimeError("broken"), "FAILED", "UNKNOWN", "FAILED_INTERNAL"),
    ],
)
def test_source_errors_are_classified(
    scan_with_integration, exception, execution, monitoring, result
):
    adapter = Mock()
    adapter.health_check.return_value = AdapterHealth(True, 4999)
    with (
        patch.object(UserIntegration, "get_token", return_value="github-token"),
        patch("scans.tasks.get_source_adapter", return_value=adapter),
        patch("scans.tasks.ScanOrchestrator") as orchestrator_class,
        pytest.raises(type(exception)),
    ):
        orchestrator_class.return_value.run.side_effect = exception
        run_scan_task(scan_with_integration.pk)

    scan_with_integration.refresh_from_db()
    assert scan_with_integration.execution_status == execution
    assert scan_with_integration.monitoring_status == monitoring
    assert scan_with_integration.result_status == result
    health = SourceHealth.objects.get(user=scan_with_integration.user, source="github")
    assert health.status in {SourceHealth.Status.WARNING, SourceHealth.Status.CRITICAL}
