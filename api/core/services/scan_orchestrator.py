import re
import hashlib
from logging import getLogger
from django.utils import timezone
from django.db.models import F
from datetime import timedelta
from scans.models import ExcludedRepository, RepositoryScanQueue, Scan, ScanRepository, SourceType
from scans.services.repositories import normalize_repository_url
from findings.models import (
    Finding,
    FindingOccurrence,
    IgnoreFindingDomain,
    IgnoreFindingType,
)
from core.models import RepoScanHistory, SystemSettings

logger = getLogger(__name__)


class ScanOrchestrator:
    """Orchestrates the end-to-end scan workflow"""

    def __init__(self, scan: Scan, source_adapter, trufflehog_client=None, detection_engines=None):
        self.scan = scan
        self.source_adapter = source_adapter
        self.detection_engines = detection_engines or ([trufflehog_client] if trufflehog_client else [])

        system_settings = SystemSettings.get_settings()
        self.skip_recent_days = system_settings.skip_recent_days
        self.verified_only = system_settings.verified_only
        self.org_repos_only = system_settings.org_repos_only
        self.repository_successes = 0
        self.repository_failures = 0

    def run(self):
        """Main orchestrator entry point"""
        logger.info(
            f"event=scan_orchestrator_started scan_id={self.scan.id} type={self.scan.type}"
        )
        try:
            self.handle_scan()
            logger.info(f"event=scan_orchestrator_completed scan_id={self.scan.id}")
        except Exception as e:
            logger.error(
                f"event=scan_orchestrator_failed scan_id={self.scan.id} error={e}",
                exc_info=True,
            )
            raise

    def handle_scan(self):
        """Handles main logic of scanning"""
        targets = self.source_adapter.search(
            self.scan.type,
            self.scan.value,
            org_repos_only=self.org_repos_only,
        )

        repository_records = self._record_discovered_targets(targets)
        active_records = [
            record for record in repository_records
            if record.status != ScanRepository.Status.EXCLUDED
        ]

        self.scan.total_repositories = len(repository_records)
        self.scan.ignored_repositories = len(repository_records) - len(active_records)
        self.scan.save(update_fields=["total_repositories", "ignored_repositories", "updated_at"])

        self._save_repository_matches(active_records)

        if self.scan.source == SourceType.YOU:
            for record in active_records:
                item, created = RepositoryScanQueue.objects.get_or_create(
                    user=self.scan.user,
                    discovery_scan=self.scan,
                    source=record.source,
                    repository_url=record.repository_url,
                    defaults={"owner": record.owner, "repository": record.repository},
                )
                record.status = ScanRepository.Status.QUEUED
                record.save(update_fields=["status", "updated_at"])
                if created:
                    from scans.tasks import process_repository_scan_queue
                    try:
                        process_repository_scan_queue.delay(item.pk)
                    except Exception as exc:
                        logger.warning(
                            "event=repository_queue_dispatch_failed queue_id=%s error=%s",
                            item.pk, exc,
                        )
            return

        logger.info(
            f"event=scan_orchestrator_targets_fetched scan_id={self.scan.id} source={self.scan.source} target_count={len(targets)}"
        )

        logger.info(
            f"event=scan_orchestrator_unique_repos_fetched scan_id={self.scan.id} repo_count={len(repository_records)}"
        )

        repos_to_scan = self.filtered_repos(active_records)

        self.scan.ignored_repositories = len(repository_records) - len(repos_to_scan)
        self.scan.save(update_fields=["ignored_repositories", "updated_at"])

        for record in repos_to_scan:
            repo = record.repository_url
            history = RepoScanHistory.objects.create(
                repository=repo, status=RepoScanHistory.ScanStatus.STARTED
            )

            record.status = ScanRepository.Status.SCANNING
            record.error_message = ""
            record.save(update_fields=["status", "error_message", "updated_at"])

            self.scan.scanned_repositories += 1
            self.scan.save()

            findings = []
            engine_successes = 0
            engine_failures = 0
            for engine in self.detection_engines:
                try:
                    findings.extend(engine.scan_repository(
                        repository_url=repo, only_verified=self.verified_only
                    ))
                    engine_successes += 1
                except Exception as e:
                    engine_failures += 1
                    logger.error(
                        "event=detection_engine_failed scan=%s repo=%s engine=%s error=%s",
                        self.scan.id, repo, getattr(engine, "name", type(engine).__name__), e,
                        exc_info=True,
                    )
            if engine_successes == 0:
                self.repository_failures += 1
                history.status = RepoScanHistory.ScanStatus.FAILED
                history.completed_at = timezone.now()
                history.save()
                record.status = ScanRepository.Status.FAILED
                record.error_message = "All detection engines failed"
                record.save(update_fields=["status", "error_message", "updated_at"])

                logger.error(
                    f"event=scan_orchestrator_repo_scan_failed scan={self.scan.id} repo={repo} error=all_detection_engines_failed",
                    exc_info=True,
                )
                continue

            if engine_failures:
                self.repository_failures += 1
                record.status = ScanRepository.Status.DEGRADED
                record.error_message = f"{engine_failures} detection engine(s) failed"
            else:
                record.status = ScanRepository.Status.COMPLETED

            history.status = RepoScanHistory.ScanStatus.COMPLETED
            history.completed_at = timezone.now()
            history.save()
            self.repository_successes += 1
            before_findings = self.scan.total_findings
            self.save_findings(repo, findings)
            record.findings_count += self.scan.total_findings - before_findings
            record.save(update_fields=["status", "error_message", "findings_count", "updated_at"])

    def _save_repository_matches(self, records):
        """Persist repository discovery as an INFO Finding, independently of secrets."""
        for record in records:
            before = self.scan.total_findings
            self.save_findings(record.repository_url, [{
                "repository": record.repository_url,
                "type": "Repository Match",
                "description": f"Repository matched monitoring query: {self.scan.value}",
                "value": record.repository_url,
                "file": "",
                "line": None,
                "author": "",
                "commit": "",
                "verified": False,
                "sensitive": False,
                "severity": Finding.Severity.INFO,
                "risk_score": 10,
                "url": record.repository_url,
            }])
            record.findings_count += self.scan.total_findings - before
            record.save(update_fields=["findings_count", "updated_at"])

    def _record_discovered_targets(self, targets):
        exclusions = {
            (item.source, item.normalized_url): item
            for item in ExcludedRepository.objects.filter(user=self.scan.user, enabled=True)
        }
        records = {}
        for target in targets:
            normalized_url = normalize_repository_url(target.url)
            key = (target.source, normalized_url)
            if key in records:
                continue
            excluded = exclusions.get(key)
            record, _ = ScanRepository.objects.update_or_create(
                scan=self.scan, source=target.source, normalized_url=normalized_url,
                defaults={
                    "repository_url": target.url, "owner": target.owner,
                    "repository": target.name,
                    "status": ScanRepository.Status.EXCLUDED if excluded else ScanRepository.Status.DISCOVERED,
                    "excluded_repository": excluded, "error_message": "",
                },
            )
            records[key] = record
        return list(records.values())

    def filtered_repos(self, repositories: list[ScanRepository]) -> list[ScanRepository]:
        """Filters repository for scanning based on different filters"""
        filterd_repositories = []
        for record in repositories:
            if self.is_recently_scanned(record.repository_url):
                logger.info(
                    f"event=scan_orchestrator_skipped_recently_scanned_repository repository={record.repository_url}"
                )
                RepoScanHistory.objects.create(
                    repository=record.repository_url,
                    status=RepoScanHistory.ScanStatus.SKIPPED,
                    completed_at=timezone.now(),
                )
                record.status = ScanRepository.Status.SKIPPED_RECENT
                record.save(update_fields=["status", "updated_at"])
            else:
                filterd_repositories.append(record)

        return filterd_repositories

    def is_recently_scanned(self, repo_url: str) -> bool:
        """Check if repository was recently scanned"""
        days = timezone.now() - timedelta(days=self.skip_recent_days)
        last_history = (
            RepoScanHistory.objects.filter(repository=repo_url)
            .order_by("-completed_at")
            .first()
        )
        if (
            last_history
            and last_history.completed_at
            and last_history.completed_at > days
        ):
            return True
        return False

    def should_ignore_finding(self, finding) -> bool:
        """Ignore findings based on the finding configuration"""
        ignored_types = set(IgnoreFindingType.objects.values_list("type", flat=True))
        ignored_domains = set(
            IgnoreFindingDomain.objects.values_list("domain", flat=True)
        )

        if finding["type"] in ignored_types:
            logger.info(
                f"event=scan_orchestrator_finding_ignored reason=type_match type={finding['type']}"
            )
            return True

        domain = self.extract_domain(finding["author"])

        if domain in ignored_domains:
            logger.info(
                f"event=scan_orchestrator_finding_ignored reason=domain_match domain={domain}"
            )
            return True

        return False

    def save_findings(self, repo_url: str, findings: list[dict]):
        """Save all findings for a given repository"""
        for finding in findings:
            if not self.should_ignore_finding(finding):
                raw_value = finding.get("value") or ""
                secret_hash = hashlib.sha256(raw_value.encode()).hexdigest()
                repository = finding.get("repository") or repo_url
                fingerprint_source = "\0".join([
                    self.scan.source,
                    repository,
                    finding.get("file") or "",
                    finding.get("type") or "",
                    secret_hash,
                ])
                fingerprint = hashlib.sha256(fingerprint_source.encode()).hexdigest()
                risk_score, severity = (
                    (finding["risk_score"], finding["severity"])
                    if "risk_score" in finding and "severity" in finding
                    else self._rate_finding(finding)
                )
                now = timezone.now()
                saved_finding, created = Finding.objects.get_or_create(
                    fingerprint=fingerprint,
                    defaults={
                        "scan": self.scan,
                        "last_scan": self.scan,
                        "source": self.scan.source,
                        "repository": repository,
                        "type": finding.get("type") or "Unknown",
                        "value": raw_value if finding.get("sensitive") is False else self._mask_secret(raw_value),
                        "secret_hash": secret_hash,
                        "description": finding.get("description") or "",
                        "file": finding.get("file") or "",
                        "line": finding.get("line"),
                        "email": finding.get("author") or "",
                        "commit_hash": finding.get("commit") or "",
                        "commit_url": finding.get("url") or f"{repo_url}/commit/{finding.get('commit') or ''}",
                        "validated": bool(finding.get("verified")),
                        "severity": severity,
                        "risk_score": risk_score,
                        "first_seen_at": now,
                        "last_seen_at": now,
                    },
                )
                if not created:
                    saved_finding.last_scan = self.scan
                    saved_finding.last_seen_at = now
                    saved_finding.validated = saved_finding.validated or bool(finding.get("verified"))
                    saved_finding.severity = severity
                    saved_finding.risk_score = risk_score
                    if saved_finding.lifecycle_status == Finding.LifecycleStatus.RESOLVED:
                        saved_finding.lifecycle_status = Finding.LifecycleStatus.REOPENED
                    saved_finding.save(update_fields=[
                        "last_scan", "last_seen_at", "validated", "severity",
                        "risk_score", "lifecycle_status", "updated_at",
                    ])
                _, occurrence_created = FindingOccurrence.objects.get_or_create(
                    finding=saved_finding, scan=self.scan
                )
                if occurrence_created:
                    if not created:
                        Finding.objects.filter(pk=saved_finding.pk).update(
                            occurrence_count=F("occurrence_count") + 1
                        )
                    self.scan.total_findings += 1
                    self.scan.save(update_fields=["total_findings", "updated_at"])
            else:
                self.scan.ignored_findings += 1
                self.scan.save()

        logger.info(
            f"event=scan_orchestrator_findings_saved scan={self.scan.id} repository={repo_url} findings_count={self.scan.total_findings}"
        )

    @staticmethod
    def _mask_secret(value: str) -> str:
        if len(value) <= 8:
            return "********"
        return f"{value[:4]}…{value[-4:]}"

    @staticmethod
    def _rate_finding(finding: dict) -> tuple[int, str]:
        finding_type = (finding.get("type") or "").lower()
        score = 20
        if any(term in finding_type for term in ("private key", "aws", "database")):
            score += 50
        elif any(term in finding_type for term in ("token", "password", "secret")):
            score += 30
        if finding.get("verified"):
            score += 20
        score += 10  # Public source exposure.
        score = min(score, 100)
        if score >= 80:
            return score, Finding.Severity.CRITICAL
        if score >= 60:
            return score, Finding.Severity.HIGH
        if score >= 40:
            return score, Finding.Severity.MEDIUM
        if score >= 20:
            return score, Finding.Severity.LOW
        return score, Finding.Severity.INFO

    @staticmethod
    def extract_domain(email: str) -> str:
        """Extracts domain from trufflehog email and returns the domain"""
        match = re.search(r"<[^@]+@([^>]+)>", email)
        return match.group(1).lower() if match else ""
