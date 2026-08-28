from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from integrations.models import UserIntegration
from integrations.tasks import run_validation_task
from core.models import SourceHealth


@pytest.mark.django_db
def test_gitlab_integration_validation_marks_connection_healthy():
    user = User.objects.create_user(username="gitlab-integration")
    integration = UserIntegration.objects.create(
        user=user,
        provider=UserIntegration.Provider.GITLAB,
        token_encrypted="encrypted",
    )
    with (
        patch.object(UserIntegration, "get_token", return_value="gitlab-token"),
        patch("integrations.tasks.validate_source_integration", return_value=(True, "")),
    ):
        run_validation_task(integration.pk)

    integration.refresh_from_db()
    assert integration.status == UserIntegration.Status.CONNECTED
    assert integration.error_message == ""
    assert integration.last_validated_at is not None
    health = SourceHealth.objects.get(user=user, source="gitlab")
    assert health.status == SourceHealth.Status.HEALTHY
    assert health.last_success_at is not None


@pytest.mark.django_db
def test_gitlab_integration_validation_preserves_failure_reason():
    user = User.objects.create_user(username="gitlab-failed")
    integration = UserIntegration.objects.create(
        user=user,
        provider=UserIntegration.Provider.GITLAB,
        token_encrypted="encrypted",
    )
    with (
        patch.object(UserIntegration, "get_token", return_value="gitlab-token"),
        patch("integrations.tasks.validate_source_integration", return_value=(False, "bad token")),
    ):
        run_validation_task(integration.pk)

    integration.refresh_from_db()
    assert integration.status == UserIntegration.Status.FAILED
    assert integration.error_message == "bad token"
    health = SourceHealth.objects.get(user=user, source="gitlab")
    assert health.status == SourceHealth.Status.WARNING
    assert health.error_message == "bad token"


@pytest.mark.django_db
def test_integration_proxy_is_encrypted_and_not_returned():
    user = User.objects.create_user(username="proxied-source")
    client = APIClient()
    client.force_authenticate(user)

    with patch("integrations.views.run_validation_task.delay"):
        response = client.post("/integrations/", {
            "provider": "github",
            "token": "github-token-value",
            "proxy_url": "socks5://proxy-user:proxy-pass@127.0.0.1:1080",
        }, format="json")

    assert response.status_code == 201
    assert response.data["proxy_configured"] is True
    assert response.data["proxy_scheme"] == "socks5"
    assert "proxy_url" not in response.data
    assert "token" not in response.data
    integration = UserIntegration.objects.get(user=user, provider="github")
    assert "proxy-pass" not in integration.proxy_url_encrypted
    assert integration.get_proxy_url() == "socks5://proxy-user:proxy-pass@127.0.0.1:1080"


@pytest.mark.django_db
def test_updating_token_without_proxy_field_preserves_proxy():
    user = User.objects.create_user(username="preserve-proxy")
    integration = UserIntegration(user=user, provider="github", token_encrypted="placeholder")
    integration.set_proxy_url("http://127.0.0.1:8080")
    integration.save()
    client = APIClient()
    client.force_authenticate(user)

    with patch("integrations.views.run_validation_task.delay"):
        response = client.post("/integrations/", {
            "provider": "github",
            "token": "replacement-token",
        }, format="json")

    assert response.status_code == 201
    integration.refresh_from_db()
    assert integration.get_proxy_url() == "http://127.0.0.1:8080"


@pytest.mark.django_db
@pytest.mark.parametrize("proxy_url", ["ftp://127.0.0.1:21", "socks5://127.0.0.1", "http://:8080", "http://127.0.0.1:99999"])
def test_invalid_proxy_is_rejected(proxy_url):
    user = User.objects.create_user(username=f"invalid-proxy-{abs(hash(proxy_url))}")
    client = APIClient()
    client.force_authenticate(user)

    response = client.post("/integrations/", {
        "provider": "github",
        "token": "github-token-value",
        "proxy_url": proxy_url,
    }, format="json")

    assert response.status_code == 400
    assert "proxy_url" in response.data
