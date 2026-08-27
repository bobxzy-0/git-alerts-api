import pytest
from django.contrib.auth.models import User

from scans.models import Scan


@pytest.mark.django_db
def test_new_scan_has_queued_unknown_status():
    user = User.objects.create_user(username="status-user", password="test-password")
    scan = Scan.objects.create(user=user, type=Scan.ScanTypes.ORG_REPOS, value="example")

    assert scan.execution_status == Scan.ExecutionStatus.QUEUED
    assert scan.monitoring_status == Scan.MonitoringStatus.UNKNOWN
    assert scan.result_status is None
    assert scan.error_code == ""
    assert scan.error_message == ""
