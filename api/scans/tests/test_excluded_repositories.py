from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.services.scan_orchestrator import ScanOrchestrator
from core.sources import RepositoryTarget
from scans.models import ExcludedRepository, RepositoryScanQueue, Scan, ScanRepository
from scans.services.repositories import normalize_repository_url


def test_repository_url_normalization_is_exact_and_stable():
    assert normalize_repository_url("HTTPS://GitHub.com/Acme/Repo.git/?ref=main") == "https://github.com/Acme/Repo"


@pytest.mark.django_db
def test_permanently_excluded_repository_never_reaches_detection_engine():
    user = User.objects.create_user(username="exclude-user")
    scan = Scan.objects.create(user=user, source="github", type="search_repos", value="acme")
    ExcludedRepository.objects.create(
        user=user, source="github", repository_url="https://github.com/acme/ignored.git",
        owner="acme", repository="ignored", reason="Known public sample",
    )
    adapter = Mock()
    adapter.search.return_value = [
        RepositoryTarget("github", "https://github.com/acme/ignored", "acme", "ignored"),
        RepositoryTarget("github", "https://github.com/acme/scanned", "acme", "scanned"),
    ]
    detector = Mock()
    detector.scan_repository.return_value = []
    with patch.object(ScanOrchestrator, "is_recently_scanned", return_value=False):
        ScanOrchestrator(scan, adapter, detector).run()

    detector.scan_repository.assert_called_once_with(
        repository_url="https://github.com/acme/scanned", only_verified=True,
    )
    excluded = ScanRepository.objects.get(scan=scan, repository="ignored")
    assert excluded.status == ScanRepository.Status.EXCLUDED
    scan.refresh_from_db()
    assert scan.total_repositories == 2
    assert scan.ignored_repositories == 1


@pytest.mark.django_db
def test_brave_does_not_enqueue_permanently_excluded_repository():
    user = User.objects.create_user(username="brave-exclude")
    scan = Scan.objects.create(user=user, source="brave", type="search_repos", value="acme")
    ExcludedRepository.objects.create(
        user=user, source="github", repository_url="https://github.com/acme/ignored",
    )
    adapter = Mock()
    adapter.search.return_value = [RepositoryTarget("github", "https://github.com/acme/ignored", "acme", "ignored")]
    with patch("scans.tasks.process_repository_scan_queue.delay") as delay:
        ScanOrchestrator(scan, adapter, Mock()).run()
    assert RepositoryScanQueue.objects.count() == 0
    assert ScanRepository.objects.get(scan=scan).status == ScanRepository.Status.EXCLUDED
    delay.assert_not_called()


@pytest.mark.django_db
def test_exclusion_api_is_user_scoped_and_rejects_duplicates():
    user = User.objects.create_user(username="exclude-api")
    other = User.objects.create_user(username="other-exclude")
    ExcludedRepository.objects.create(user=other, source="github", repository_url="https://github.com/acme/other")
    client = APIClient()
    client.force_authenticate(user)
    payload = {
        "source": "github", "repository_url": "https://github.com/acme/repo.git",
        "owner": "acme", "repository": "repo", "reason": "Not in monitoring scope",
    }
    assert client.post("/excluded-repositories/", payload, format="json").status_code == 201
    assert client.post("/excluded-repositories/", {**payload, "repository_url": "https://github.com/acme/repo/"}, format="json").status_code == 400
    items = client.get("/excluded-repositories/").json()
    assert len(items) == 1
    assert items[0]["reason"] == "Not in monitoring scope"


@pytest.mark.django_db
def test_scan_repository_api_only_returns_owned_scan():
    user = User.objects.create_user(username="repo-list")
    other = User.objects.create_user(username="repo-list-other")
    own_scan = Scan.objects.create(user=user, value="own")
    other_scan = Scan.objects.create(user=other, value="other")
    ScanRepository.objects.create(scan=own_scan, source="github", repository_url="https://github.com/acme/own", normalized_url="https://github.com/acme/own")
    client = APIClient()
    client.force_authenticate(user)
    assert client.get(f"/scans/{own_scan.pk}/repositories/").status_code == 200
    assert client.get(f"/scans/{other_scan.pk}/repositories/").status_code == 404
