from logging import getLogger
from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from .models import MonitorRule, RepositoryScanQueue, Scan
from integrations.models import UserIntegration
from core.sources import (
    SourceAuthError, SourceNetworkError, SourceRateLimitError,
    SourceResponseError, get_source_adapter,
)
from core.models import SourceHealth
from findings.models import FindingOccurrence
from core.detection import get_detection_engines
from core.services.scan_orchestrator import ScanOrchestrator

logger = getLogger(__name__)


@shared_task
def process_repository_scan_queue(queue_id):
    item = RepositoryScanQueue.objects.select_related("discovery_scan").get(pk=queue_id)
    if item.status != RepositoryScanQueue.Status.QUEUED:
        return item.scan_id
    item.status = RepositoryScanQueue.Status.RUNNING
    item.save(update_fields=["status", "updated_at"])
    try:
        integration_exists = UserIntegration.objects.filter(
            user=item.user, provider=item.source, status=UserIntegration.Status.CONNECTED
        ).exists()
        if not integration_exists:
            raise SourceAuthError(f"{item.source.title()} integration is required for repository scan")
        scan = Scan.objects.create(
            user=item.user, source=item.source, type=Scan.ScanTypes.REPOSITORY,
            value=item.repository_url, trigger_type=Scan.TriggerTypes.REPOSITORY_QUEUE,
        )
        item.scan = scan
        item.save(update_fields=["scan", "updated_at"])
        run_scan_task(scan.pk)
        item.status = RepositoryScanQueue.Status.COMPLETED
        item.save(update_fields=["status", "updated_at"])
        return scan.pk
    except Exception as exc:
        item.status = RepositoryScanQueue.Status.FAILED
        item.error_message = str(exc)
        item.save(update_fields=["status", "error_message", "updated_at"])
        raise


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
            user=scan.user, provider=scan.source
        ).first()

        if integration is None:
            source_name = scan.source.upper()
            message = f"{scan.source.title()} integration is not configured"
            _mark_failed(scan, Scan.ResultStatus.FAILED_AUTH, f"{source_name}_INTEGRATION_MISSING", message)
            raise SourceAuthError(message)

        source_token = integration.get_token()

        logger.info(
            f"event=scan_preflight_validation scan_id={scan_id} integration_id={integration.id}"
        )
        proxy_url = integration.get_proxy_url()
        source_adapter = get_source_adapter(scan.source, token=source_token, proxy_url=proxy_url)
        adapter_health = source_adapter.health_check()
        integration.status = UserIntegration.Status.CONNECTED
        integration.error_message = ""
        integration.last_validated_at = timezone.now()
        integration.save(update_fields=["status", "error_message", "last_validated_at", "updated_at"])
        SourceHealth.objects.update_or_create(
            user=scan.user,
            source=scan.source,
            defaults={
                "status": SourceHealth.Status.HEALTHY,
                "last_checked_at": timezone.now(),
                "rate_limit_remaining": adapter_health.rate_limit_remaining,
                "error_code": "",
                "error_message": "",
            },
        )

        orchestrator = ScanOrchestrator(
            scan=scan,
            source_adapter=source_adapter,
            detection_engines=get_detection_engines(scan.user, proxy_url=proxy_url),
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
        _record_source_scan(scan)
        from notifications.tasks import queue_scan_alerts
        queue_scan_alerts.delay(scan.pk)
        logger.info(f"event=scan_completed scan_id={scan_id}")

    except SourceAuthError as e:
        logger.error(
            f"event=scan_auth_failed scan_id={scan_id} error={e}", exc_info=True
        )

        if integration:
            integration.status = UserIntegration.Status.FAILED
            integration.error_message = f"{scan.source.title()} token is invalid or expired"
            integration.last_validated_at = timezone.now()
            integration.save()

            logger.info(
                f"event=integration_marked_failed integration_id={integration.id} reason=auth_error"
            )

        if scan:
            code = f"{scan.source.upper()}_AUTH_FAILED"
            _mark_failed(scan, Scan.ResultStatus.FAILED_AUTH, code, str(e))
            _record_source_failure(scan, SourceHealth.Status.CRITICAL, code, str(e))

        raise

    except SourceRateLimitError as e:
        logger.warning(f"event=scan_rate_limited scan_id={scan_id} error={e}")
        if scan:
            scan.execution_status = Scan.ExecutionStatus.DEGRADED
            scan.monitoring_status = Scan.MonitoringStatus.WARNING
            scan.result_status = Scan.ResultStatus.DEGRADED_RATE_LIMIT
            scan.error_code = f"{scan.source.upper()}_RATE_LIMIT"
            scan.error_message = str(e)
            scan.completed_at = timezone.now()
            scan.save(update_fields=[
                "execution_status", "monitoring_status", "result_status",
                "error_code", "error_message", "completed_at", "updated_at",
            ])
            _record_source_failure(scan, SourceHealth.Status.WARNING, scan.error_code, str(e))
        raise

    except SourceNetworkError as e:
        logger.error(f"event=scan_network_failed scan_id={scan_id} error={e}", exc_info=True)
        if scan:
            code = f"{scan.source.upper()}_NETWORK_FAILED"
            _mark_failed(scan, Scan.ResultStatus.FAILED_NETWORK, code, str(e))
            _record_source_failure(scan, SourceHealth.Status.WARNING, code, str(e))
        raise

    except SourceResponseError as e:
        logger.error(f"event=scan_response_failed scan_id={scan_id} error={e}", exc_info=True)
        if scan:
            code = f"{scan.source.upper()}_RESPONSE_INVALID"
            _mark_failed(scan, Scan.ResultStatus.FAILED_INTERNAL, code, str(e))
            _record_source_failure(scan, SourceHealth.Status.CRITICAL, code, str(e))
        raise

    except Exception as e:
        logger.error(f"event=scan_failed scan_id={scan_id} error={e}", exc_info=True)
        if scan:
            _mark_failed(scan, Scan.ResultStatus.FAILED_INTERNAL, "SCAN_INTERNAL_ERROR", str(e))
            _record_source_failure(scan, SourceHealth.Status.CRITICAL, "SCAN_INTERNAL_ERROR", str(e))
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


def _record_source_scan(scan):
    now = timezone.now()
    new_findings = FindingOccurrence.objects.filter(
        scan=scan, finding__scan=scan
    ).count()
    status = (
        SourceHealth.Status.HEALTHY
        if scan.execution_status == Scan.ExecutionStatus.SUCCESS
        else SourceHealth.Status.WARNING
    )
    SourceHealth.objects.update_or_create(
        user=scan.user,
        source=scan.source,
        defaults={
            "status": status,
            "last_checked_at": now,
            "last_success_at": now,
            "result_count": scan.total_repositories,
            "new_findings": new_findings,
            "error_code": scan.error_code,
            "error_message": scan.error_message,
        },
    )


def _record_source_failure(scan, status, error_code, error_message):
    now = timezone.now()
    SourceHealth.objects.update_or_create(
        user=scan.user,
        source=scan.source,
        defaults={
            "status": status,
            "last_checked_at": now,
            "last_failure_at": now,
            "error_code": error_code,
            "error_message": error_message,
        },
    )


@shared_task(ignore_result=True)
def dispatch_due_monitor_rules():
    """Claim due rules, create visible scan records, then enqueue execution.

    Creating the Scan here is intentional: Beat dispatch must be observable even
    when a worker is unavailable or the broker rejects the execution task.
    """
    now = timezone.now()
    stale_before = now - timedelta(hours=12)
    MonitorRule.objects.filter(is_running=True, locked_at__lt=stale_before).update(
        is_running=False, locked_at=None
    )
    # Recover locks left by the previous dispatcher, which claimed a rule
    # before creating its Scan in a second worker task. New dispatches always
    # attach last_scan before enqueueing, so this targets legacy orphans only.
    orphaned_before = now - timedelta(minutes=5)
    MonitorRule.objects.filter(
        is_running=True,
        last_scan__isnull=True,
        locked_at__lt=orphaned_before,
    ).update(is_running=False, locked_at=None)

    rule_ids = list(
        MonitorRule.objects.filter(
            enabled=True,
            is_running=False,
            next_run_at__lte=now,
        ).values_list("id", flat=True)
    )
    dispatched = 0
    for rule_id in rule_ids:
        claimed = MonitorRule.objects.filter(
            pk=rule_id,
            enabled=True,
            is_running=False,
            next_run_at__lte=now,
        ).update(is_running=True, locked_at=now)
        if claimed:
            rule = MonitorRule.objects.select_related("user").get(pk=rule_id)
            scan = Scan.objects.create(
                user=rule.user,
                source=rule.source,
                type=rule.scan_type,
                value=rule.value,
                trigger_type=Scan.TriggerTypes.SCHEDULED,
                monitor_rule=rule,
            )
            MonitorRule.objects.filter(pk=rule_id).update(last_scan=scan)
            try:
                run_monitor_rule_task.delay(rule_id, scan.pk)
                dispatched += 1
            except Exception as exc:
                logger.exception(
                    "event=monitor_rule_dispatch_failed rule_id=%s scan_id=%s",
                    rule_id,
                    scan.pk,
                )
                completed_at = timezone.now()
                scan.execution_status = Scan.ExecutionStatus.FAILED
                scan.monitoring_status = Scan.MonitoringStatus.UNKNOWN
                scan.result_status = Scan.ResultStatus.FAILED_INTERNAL
                scan.error_code = "MONITOR_DISPATCH_FAILED"
                scan.error_message = str(exc)
                scan.completed_at = completed_at
                scan.save(update_fields=[
                    "execution_status", "monitoring_status", "result_status",
                    "error_code", "error_message", "completed_at", "updated_at",
                ])
                MonitorRule.objects.filter(pk=rule_id).update(
                    last_run_at=completed_at,
                    next_run_at=rule.next_occurrence(completed_at),
                    is_running=False,
                    locked_at=None,
                )
    return dispatched


@shared_task
def run_monitor_rule_task(rule_id, scan_id=None, preserve_next_run=False):
    """Execute one claimed rule and always release its concurrency lock."""
    rule = MonitorRule.objects.select_related("user").get(pk=rule_id)
    # A scan_id means Beat already claimed this run while the rule was enabled.
    # Finish that observable run even if the user disables future scheduling in
    # the small window between dispatch and worker execution.
    if not rule.enabled and scan_id is None:
        MonitorRule.objects.filter(pk=rule_id).update(is_running=False, locked_at=None)
        return None

    scan = (
        Scan.objects.get(pk=scan_id, user=rule.user)
        if scan_id is not None
        else Scan.objects.create(
            user=rule.user,
            source=rule.source,
            type=rule.scan_type,
            value=rule.value,
            trigger_type=Scan.TriggerTypes.SCHEDULED,
            monitor_rule=rule,
        )
    )
    MonitorRule.objects.filter(pk=rule_id).update(last_scan=scan)
    try:
        run_scan_task(scan.pk)
        return scan.pk
    finally:
        completed_at = timezone.now()
        updates = dict(
            last_run_at=completed_at,
            is_running=False,
            locked_at=None,
        )
        if not preserve_next_run:
            updates["next_run_at"] = rule.next_occurrence(completed_at)
        MonitorRule.objects.filter(pk=rule_id).update(**updates)
