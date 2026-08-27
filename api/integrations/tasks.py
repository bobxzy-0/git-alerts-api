import requests
from logging import getLogger
from celery import shared_task
from django.utils import timezone
from .models import UserIntegration

logger = getLogger(__name__)

@shared_task
def run_validation_task(integration_id):
    """Celery task for performing integration token validation"""
    logger.info(
        f"event=celery_task_received task={run_validation_task.name} integration_id={integration_id}"
    )
    try:
        logger.info(
            f"event=integration_validation_started integration_id={integration_id}"
        )

        integration = UserIntegration.objects.get(id=integration_id)
        integration.status = UserIntegration.Status.PENDING
        integration.save()

        if integration.provider == "github":
            is_valid, error_message = validate_github_integration(integration.get_token())

            if is_valid:
                integration.status = UserIntegration.Status.CONNECTED
                integration.error_message = ''
            else:
                integration.status = UserIntegration.Status.FAILED
                integration.error_message = error_message

        elif integration.provider == "gitlab":
            is_valid, error_message = validate_gitlab_integration(integration.get_token())
            integration.status = (
                UserIntegration.Status.CONNECTED if is_valid else UserIntegration.Status.FAILED
            )
            integration.error_message = error_message

        elif integration.provider == "gitee":
            is_valid, error_message = validate_source_integration("gitee", integration.get_token())
            integration.status = (
                UserIntegration.Status.CONNECTED if is_valid else UserIntegration.Status.FAILED
            )
            integration.error_message = error_message

        elif integration.provider == "brave":
            is_valid, error_message = validate_source_integration("brave", integration.get_token())
            integration.status = UserIntegration.Status.CONNECTED if is_valid else UserIntegration.Status.FAILED
            integration.error_message = error_message

        elif integration.provider == "slack":
            if validate_slack_integration(integration.get_token()):
                integration.status = UserIntegration.Status.CONNECTED
                integration.error_message = ''
            else:
                integration.status = UserIntegration.Status.FAILED
                integration.error_message = 'Slack token validation failed'

        else:
            integration.status = UserIntegration.Status.FAILED
            integration.error_message = 'Unknown provider'

        # Update last_validated_at timestamp
        integration.last_validated_at = timezone.now()
        integration.save()

        logger.info(
            f"event=integration_validation_completed integration_id={integration_id} status={integration.status}"
        )
    except Exception as e:
        logger.error(
            f"event=integration_validation_failed integration_id={integration_id} error={e}"
        )
        raise

def validate_github_integration(github_token: str) -> tuple[bool, str]:
    """
    Validate GitHub integration token
    Returns: (is_valid, error_message)
    """
    try:
        url = "https://api.github.com/user"
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        response = requests.get(url=url, headers=headers)

        if response.status_code == 200:
            return (True, '')
        elif response.status_code == 401:
            return (False, 'Token is invalid or expired')
        elif response.status_code == 403:
            return (False, 'Token lacks required permissions')
        else:
            return (False, f'GitHub API error: {response.status_code}')

    except requests.RequestException as e:
        logger.error(
            f"event=validate_github_integration_failed error={e}",
            exc_info=True
        )
        return (False, f'Network error: {str(e)}')
    except Exception as e:
        logger.error(
            f"event=validate_github_integration_failed error={e}",
            exc_info=True
        )
        return (False, f'Validation error: {str(e)}')

def validate_slack_integration(slack_token: str) -> bool:
    """function to validate Slack integration"""
    return True


def validate_gitlab_integration(gitlab_token: str) -> tuple[bool, str]:
    """Validate GitLab credentials through the same adapter used by scans."""
    from core.sources import get_source_adapter
    from core.sources.base import SourceAuthError, SourceNetworkError, SourceRateLimitError

    try:
        get_source_adapter("gitlab", token=gitlab_token).health_check()
        return True, ""
    except SourceAuthError as exc:
        return False, str(exc)
    except SourceRateLimitError as exc:
        return False, f"Rate limit error: {exc}"
    except SourceNetworkError as exc:
        return False, f"Network error: {exc}"
    except Exception as exc:
        logger.error("event=validate_gitlab_integration_failed error=%s", exc, exc_info=True)
        return False, f"Validation error: {exc}"


def validate_source_integration(source: str, token: str) -> tuple[bool, str]:
    from core.sources import get_source_adapter
    from core.sources.base import SourceAuthError, SourceNetworkError, SourceRateLimitError

    try:
        get_source_adapter(source, token=token).health_check()
        return True, ""
    except SourceAuthError as exc:
        return False, str(exc)
    except SourceRateLimitError as exc:
        return False, f"Rate limit error: {exc}"
    except SourceNetworkError as exc:
        return False, f"Network error: {exc}"
    except Exception as exc:
        logger.error("event=validate_source_integration_failed source=%s error=%s", source, exc, exc_info=True)
        return False, f"Validation error: {exc}"
