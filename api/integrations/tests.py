from unittest.mock import patch

import pytest
from django.contrib.auth.models import User

from integrations.models import UserIntegration
from integrations.tasks import run_validation_task


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
        patch("integrations.tasks.validate_gitlab_integration", return_value=(True, "")),
    ):
        run_validation_task(integration.pk)

    integration.refresh_from_db()
    assert integration.status == UserIntegration.Status.CONNECTED
    assert integration.error_message == ""
    assert integration.last_validated_at is not None


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
        patch("integrations.tasks.validate_gitlab_integration", return_value=(False, "bad token")),
    ):
        run_validation_task(integration.pk)

    integration.refresh_from_db()
    assert integration.status == UserIntegration.Status.FAILED
    assert integration.error_message == "bad token"
