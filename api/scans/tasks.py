from logging import getLogger
from celery import shared_task
from django.utils import timezone
from .models import Scan
from integrations.models import UserIntegration
from integrations.tasks import validate_github_integration
from core.clients.github_client import (
    GitHubClient,
    GitHubAPIError,
    GitHubAuthError,
    GitHubRateLimitError,
)
from core.clients.trufflehog_client import TruffleHogClient
from core.services.scan_orchestrator import ScanOrchestrator

logger = getLogger(__name__)


@shared_task
def run_scan_task(scan_id):
    """Celery task for the scanning"""
    logger.info(
        f"event=celery_task_received task={run_scan_task.name} scan_id={scan_id}"
    )

    scan = None
    integration = None

    try:
        logger.info(f"event=scan_started scan_id={scan_id}")
        scan = Scan.objects.get(id=scan_id)
        scan.execution_status = Scan.ExecutionStatus.RUNNING
        scan.monitoring_status = Scan.MonitoringStatus.UNKNOWN
        scan.result_status = None
        scan.error_code = ""
        scan.error_message = ""
        scan.started_at = timezone.now()
        scan.completed_at = None
        scan.save(update_fields=[
            "execution_status", "monitoring_status", "result_status",
            "error_code", "error_message", "started_at", "completed_at", "updated_at",
        ])

        integration = UserIntegration.objects.filter(
            user=scan.user, provider=UserIntegration.Provider.GITHUB
        ).first()

        if integration is None:
            _mark_failed(scan, Scan.ResultStatus.FAILED_AUTH, "GITHUB_INTEGRATION_MISSING", "GitHub integration is not configured")
            raise GitHubAuthError("GitHub integration is not configured")

        github_token = integration.get_token()

        logger.info(
            f"event=scan_preflight_validation scan_id={scan_id} integration_id={integration.id}"
        )
        is_valid, error_message = validate_github_integration(github_token)

        if not is_valid:
            integration.status = UserIntegration.Status.FAILED
            integration.error_message = error_message
            integration.last_validated_at = timezone.now()
            integration.save()

            logger.error(
                f"event=scan_preflight_failed scan_id={scan_id} integration_id={integration.id} reason={error_message}"
            )

            result_status = (
                Scan.ResultStatus.FAILED_NETWORK
                if error_message.lower().startswith("network error")
                else Scan.ResultStatus.FAILED_AUTH
            )
            _mark_failed(scan, result_status, "GITHUB_PREFLIGHT_FAILED", error_message)
            if result_status == Scan.ResultStatus.FAILED_NETWORK:
                raise GitHubAPIError(error_message)
            raise GitHubAuthError(error_message)

        integration.last_validated_at = timezone.now()
        integration.save()

        logger.info(
            f"event=scan_preflight_passed scan_id={scan_id} integration_id={integration.id}"
        )

        orchestrator = ScanOrchestrator(
            scan=scan,
            github_client=GitHubClient(token=github_token),
            trufflehog_client=TruffleHogClient(),
        )

        orchestrator.run()

        # The orchestrator and future detection workers may update counters via
        # separate ORM queries. Always classify from the committed DB values.
        scan.refresh_from_db(fields=["total_repositories", "total_findings"])

        if orchestrator.repository_failures:
            all_repositories_failed = (
                orchestrator.repository_successes == 0 and scan.total_repositories > 0
            )
            scan.execution_status = (
                Scan.ExecutionStatus.FAILED
                if all_repositories_failed
                else Scan.ExecutionStatus.DEGRADED
            )
            scan.monitoring_status = (
                Scan.MonitoringStatus.UNKNOWN
                if all_repositories_failed
                else Scan.MonitoringStatus.WARNING
            )
            scan.result_status = Scan.ResultStatus.FAILED_INTERNAL
            scan.error_code = (
                "REPOSITORY_SCAN_FAILED"
                if all_repositories_failed
                else "REPOSITORY_SCAN_PARTIAL_FAILURE"
            )
            scan.error_message = f"{orchestrator.repository_failures} repository scan(s) failed"
        else:
            scan.execution_status = Scan.ExecutionStatus.SUCCESS
            scan.monitoring_status = (
                Scan.MonitoringStatus.HEALTHY
                if scan.total_findings == 0
                else Scan.MonitoringStatus.WARNING
            )
            if scan.total_repositories == 0:
                scan.result_status = Scan.ResultStatus.HEALTHY_TARGET_ABSENT
            elif scan.total_findings == 0:
                scan.result_status = Scan.ResultStatus.HEALTHY_NO_FINDINGS
            else:
                # Finding severity is introduced in a later phase. Until then,
                # existing findings use the conservative MEDIUM result bucket.
                scan.result_status = Scan.ResultStatus.FINDINGS_MEDIUM
        scan.completed_at = timezone.now()
        scan.save(update_fields=[
            "execution_status", "monitoring_status", "result_status",
            "error_code", "error_message", "completed_at", "updated_at",
        ])
        logger.info(f"event=scan_completed scan_id={scan_id}")

    except GitHubAuthError as e:
        logger.error(
            f"event=scan_auth_failed scan_id={scan_id} error={e}", exc_info=True
        )

        if integration:
            integration.status = UserIntegration.Status.FAILED
            integration.error_message = "GitHub token is invalid or expired"
            integration.last_validated_at = timezone.now()
            integration.save()

            logger.info(
                f"event=integration_marked_failed integration_id={integration.id} reason=auth_error"
            )

        if scan:
            _mark_failed(scan, Scan.ResultStatus.FAILED_AUTH, "GITHUB_AUTH_FAILED", str(e))

        raise

    except GitHubRateLimitError as e:
        logger.warning(f"event=scan_rate_limited scan_id={scan_id} error={e}")
        if scan:
            scan.execution_status = Scan.ExecutionStatus.DEGRADED
            scan.monitoring_status = Scan.MonitoringStatus.WARNING
            scan.result_status = Scan.ResultStatus.DEGRADED_RATE_LIMIT
            scan.error_code = "GITHUB_RATE_LIMIT"
            scan.error_message = str(e)
            scan.completed_at = timezone.now()
            scan.save(update_fields=[
                "execution_status", "monitoring_status", "result_status",
                "error_code", "error_message", "completed_at", "updated_at",
            ])
        raise

    except GitHubAPIError as e:
        logger.error(f"event=scan_network_failed scan_id={scan_id} error={e}", exc_info=True)
        if scan:
            _mark_failed(scan, Scan.ResultStatus.FAILED_NETWORK, "GITHUB_NETWORK_FAILED", str(e))
        raise

    except Exception as e:
        logger.error(f"event=scan_failed scan_id={scan_id} error={e}", exc_info=True)
        if scan:
            _mark_failed(scan, Scan.ResultStatus.FAILED_INTERNAL, "SCAN_INTERNAL_ERROR", str(e))
        raise


def _mark_failed(scan, result_status, error_code, error_message):
    scan.execution_status = Scan.ExecutionStatus.FAILED
    scan.monitoring_status = Scan.MonitoringStatus.UNKNOWN
    scan.result_status = result_status
    scan.error_code = error_code
    scan.error_message = error_message
    scan.completed_at = timezone.now()
    scan.save(update_fields=[
        "execution_status", "monitoring_status", "result_status",
        "error_code", "error_message", "completed_at", "updated_at",
    ])
