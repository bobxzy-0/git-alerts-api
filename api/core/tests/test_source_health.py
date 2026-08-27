import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models import SourceHealth


@pytest.mark.django_db
def test_source_health_api_is_user_scoped():
    user = User.objects.create_user(username="health-user", password="test-password")
    other = User.objects.create_user(username="other-health", password="test-password")
    SourceHealth.objects.create(user=user, source="github", status="HEALTHY")
    SourceHealth.objects.create(user=other, source="gitee", status="WARNING")

    client = APIClient()
    client.force_authenticate(user)
    response = client.get("/source-health/")

    assert response.status_code == 200
    assert [item["source"] for item in response.json()] == ["github"]
