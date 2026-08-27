from unittest.mock import Mock, patch

import pytest
import requests

from core.clients.gitlab_client import GitLabClient
from core.sources import (
    SourceAuthError, SourceNetworkError, SourceRateLimitError, SourceResponseError,
)


def response(status=200, payload=None, headers=None):
    result = Mock()
    result.status_code = status
    result.ok = 200 <= status < 300
    result.headers = headers or {}
    result.text = ""
    result.json.return_value = payload
    return result


def test_gitlab_pagination_uses_next_page_header():
    first = response(200, [{"id": 1}], {"X-Next-Page": "2"})
    second = response(200, [{"id": 2}], {"X-Next-Page": ""})
    client = GitLabClient("token")
    with patch("requests.request", side_effect=[first, second]) as request:
        assert client.search_projects("acme") == [{"id": 1}, {"id": 2}]
    assert request.call_args_list[1].kwargs["params"]["page"] == "2"


@pytest.mark.parametrize(
    ("status", "error"),
    [(401, SourceAuthError), (403, SourceAuthError), (429, SourceRateLimitError),
     (500, SourceNetworkError), (422, SourceResponseError)],
)
def test_gitlab_http_errors_are_classified_before_json(status, error):
    result = response(status)
    with patch("requests.request", return_value=result), pytest.raises(error):
        GitLabClient("token").get_current_user()
    result.json.assert_not_called()


def test_gitlab_invalid_json_is_classified():
    result = response(200)
    result.json.side_effect = requests.exceptions.JSONDecodeError("bad", "", 0)
    with patch("requests.request", return_value=result), pytest.raises(SourceResponseError):
        GitLabClient("token").get_current_user()


def test_gitlab_paginated_payload_must_be_list():
    with patch("requests.request", return_value=response(200, {"items": []})), pytest.raises(SourceResponseError):
        GitLabClient("token").search_projects("acme")
