from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User

from core.services.scan_orchestrator import ScanOrchestrator
from scans.models import Scan


@pytest.mark.django_db
def test_orchestrator_counts_repository_failures_without_aborting_scan():
    user = User.objects.create_user(username="orchestrator-user", password="test-password")
    scan = Scan.objects.create(user=user, type=Scan.ScanTypes.ORG_REPOS, value="example")
    github_client = Mock()
    github_client.get_org_repos.return_value = [
        {"html_url": "https://github.com/example/ok"},
        {"html_url": "https://github.com/example/fails"},
    ]
    trufflehog_client = Mock()
    trufflehog_client.scan_repository.side_effect = [[], RuntimeError("scanner failed")]

    with patch.object(ScanOrchestrator, "is_recently_scanned", return_value=False):
        orchestrator = ScanOrchestrator(scan, github_client, trufflehog_client)
        orchestrator.run()

    assert orchestrator.repository_successes == 1
    assert orchestrator.repository_failures == 1
    scan.refresh_from_db()
    assert scan.total_findings == 0
