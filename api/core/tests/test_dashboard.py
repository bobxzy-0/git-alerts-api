import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models import SourceHealth
from scans.models import Scan


@pytest.mark.django_db
def test_dashboard_returns_aggregated_monitoring_data():
    user = User.objects.create_user(username="dashboard-user", password="test-password")
    SourceHealth.objects.create(user=user, source="github", status="HEALTHY", result_count=3)
    Scan.objects.create(user=user, type="org_repos", value="example")
    client = APIClient()
    client.force_authenticate(user)

    response = client.get("/dashboard/")

    assert response.status_code == 200
    data = response.json()
    assert data["overall_health"] == "HEALTHY"
    assert data["source_health"][0]["source"] == "github"
    assert data["severity_counts"] == {
        "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0,
    }
    assert len(data["recent_scans"]) == 1
