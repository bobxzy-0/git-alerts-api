from unittest.mock import Mock

import pytest
from django.contrib.auth.models import User

from core.services.scan_orchestrator import ScanOrchestrator
from findings.models import Finding, FindingOccurrence
from scans.models import Scan


def detected_secret(value="super-secret-value", verified=True):
    return {
        "repository": "https://github.com/example/repo",
        "type": "AWS Access Key",
        "value": value,
        "description": "AWS credential",
        "file": "settings.py",
        "line": 10,
        "author": "User <user@example.com>",
        "commit": "abc123",
        "verified": verified,
    }


@pytest.fixture
def scans(db):
    user = User.objects.create_user(username="finding-user", password="test-password")
    return (
        Scan.objects.create(user=user, type=Scan.ScanTypes.ORG_REPOS, value="example"),
        Scan.objects.create(user=user, type=Scan.ScanTypes.ORG_REPOS, value="example"),
    )


def orchestrator(scan):
    return ScanOrchestrator(scan, Mock(), Mock())


@pytest.mark.django_db
def test_same_finding_is_deduplicated_across_scans(scans):
    first_scan, second_scan = scans
    orchestrator(first_scan).save_findings("https://github.com/example/repo", [detected_secret()])
    orchestrator(second_scan).save_findings("https://github.com/example/repo", [detected_secret()])

    assert Finding.objects.count() == 1
    finding = Finding.objects.get()
    assert finding.occurrence_count == 2
    assert FindingOccurrence.objects.filter(finding=finding).count() == 2
    assert finding.value == "supe…alue"
    assert finding.value != "super-secret-value"
    assert len(finding.secret_hash) == 64
    assert len(finding.fingerprint) == 64


@pytest.mark.django_db
def test_resolved_finding_becomes_reopened(scans):
    first_scan, second_scan = scans
    orchestrator(first_scan).save_findings("https://github.com/example/repo", [detected_secret()])
    finding = Finding.objects.get()
    finding.lifecycle_status = Finding.LifecycleStatus.RESOLVED
    finding.save(update_fields=["lifecycle_status"])

    orchestrator(second_scan).save_findings("https://github.com/example/repo", [detected_secret()])

    finding.refresh_from_db()
    assert finding.lifecycle_status == Finding.LifecycleStatus.REOPENED


@pytest.mark.django_db
def test_different_secret_has_different_fingerprint(scans):
    first_scan, _ = scans
    orchestrator(first_scan).save_findings(
        "https://github.com/example/repo",
        [detected_secret("first-secret"), detected_secret("second-secret")],
    )
    assert Finding.objects.count() == 2


@pytest.mark.django_db
def test_verified_aws_key_is_critical(scans):
    first_scan, _ = scans
    orchestrator(first_scan).save_findings("https://github.com/example/repo", [detected_secret()])
    finding = Finding.objects.get()
    assert finding.severity == Finding.Severity.CRITICAL
    assert finding.risk_score >= 80
