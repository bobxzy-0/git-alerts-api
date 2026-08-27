from unittest.mock import patch

import pytest
from django.contrib.auth.models import User

from core.clients.github_client import GitHubAPIError, GitHubAuthError, GitHubRateLimitError
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

    with (
        patch.object(UserIntegration, "get_token", return_value="github-token"),
        patch("scans.tasks.validate_github_integration", return_value=(True, "")),
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


@pytest.mark.django_db
def test_zero_findings_are_healthy_not_failed(scan_with_integration):
    scan = run_with_orchestrator(
        scan_with_integration, repositories=2, findings=0, successes=2
    )

    assert scan.execution_status == Scan.ExecutionStatus.SUCCESS
    assert scan.monitoring_status == Scan.MonitoringStatus.HEALTHY
    assert scan.result_status == Scan.ResultStatus.HEALTHY_NO_FINDINGS


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
        (GitHubAuthError("bad token"), "FAILED", "UNKNOWN", "FAILED_AUTH"),
        (GitHubAPIError("network down"), "FAILED", "UNKNOWN", "FAILED_NETWORK"),
        (GitHubRateLimitError("limited"), "DEGRADED", "WARNING", "DEGRADED_RATE_LIMIT"),
        (RuntimeError("broken"), "FAILED", "UNKNOWN", "FAILED_INTERNAL"),
    ],
)
def test_source_errors_are_classified(
    scan_with_integration, exception, execution, monitoring, result
):
    with (
        patch.object(UserIntegration, "get_token", return_value="github-token"),
        patch("scans.tasks.validate_github_integration", return_value=(True, "")),
        patch("scans.tasks.ScanOrchestrator") as orchestrator_class,
        pytest.raises(type(exception)),
    ):
        orchestrator_class.return_value.run.side_effect = exception
        run_scan_task(scan_with_integration.pk)

    scan_with_integration.refresh_from_db()
    assert scan_with_integration.execution_status == execution
    assert scan_with_integration.monitoring_status == monitoring
    assert scan_with_integration.result_status == result
