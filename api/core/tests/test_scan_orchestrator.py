from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User

from core.services.scan_orchestrator import ScanOrchestrator
from core.sources import RepositoryTarget
from scans.models import RepositoryScanQueue, Scan


@pytest.mark.django_db
def test_orchestrator_counts_repository_failures_without_aborting_scan():
    user = User.objects.create_user(username="orchestrator-user", password="test-password")
    scan = Scan.objects.create(user=user, type=Scan.ScanTypes.ORG_REPOS, value="example")
    source_adapter = Mock()
    source_adapter.search.return_value = [
        RepositoryTarget("github", "https://github.com/example/ok", "example", "ok"),
        RepositoryTarget("github", "https://github.com/example/fails", "example", "fails"),
    ]
    trufflehog_client = Mock()
    trufflehog_client.scan_repository.side_effect = [[], RuntimeError("scanner failed")]

    with patch.object(ScanOrchestrator, "is_recently_scanned", return_value=False):
        orchestrator = ScanOrchestrator(scan, source_adapter, trufflehog_client)
        orchestrator.run()

    assert orchestrator.repository_successes == 1
    assert orchestrator.repository_failures == 1
    scan.refresh_from_db()
    assert scan.total_findings == 0


@pytest.mark.django_db
def test_brave_discovery_enqueues_repositories_without_scanning_search_results():
    user = User.objects.create_user(username="brave-user")
    scan = Scan.objects.create(user=user, source="brave", type=Scan.ScanTypes.SEARCH_REPOS, value="acme")
    source_adapter = Mock()
    source_adapter.search.return_value = [
        RepositoryTarget("github", "https://github.com/acme/api", "acme", "api")
    ]
    detector = Mock()
    with patch("scans.tasks.process_repository_scan_queue.delay") as delay:
        ScanOrchestrator(scan, source_adapter, detector).run()

    item = RepositoryScanQueue.objects.get(discovery_scan=scan)
    assert item.source == "github"
    assert item.status == RepositoryScanQueue.Status.QUEUED
    delay.assert_called_once_with(item.pk)
    detector.scan_repository.assert_not_called()


@pytest.mark.django_db
def test_one_detection_engine_failure_keeps_other_engine_findings():
    user = User.objects.create_user(username="multi-engine")
    scan = Scan.objects.create(user=user, type=Scan.ScanTypes.ORG_REPOS, value="example")
    adapter = Mock()
    adapter.search.return_value = [RepositoryTarget("github", "https://github.com/acme/api", "acme", "api")]
    failed = Mock(name="failed-engine")
    failed.scan_repository.side_effect = RuntimeError("engine unavailable")
    healthy = Mock(name="healthy-engine")
    healthy.scan_repository.return_value = []
    with patch.object(ScanOrchestrator, "is_recently_scanned", return_value=False):
        orchestrator = ScanOrchestrator(scan, adapter, detection_engines=[failed, healthy])
        orchestrator.run()
    assert orchestrator.repository_successes == 1
    assert orchestrator.repository_failures == 1
