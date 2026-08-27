from unittest.mock import Mock, patch

import pytest
import requests

from core.clients.gitee_client import GiteeClient
from core.sources import SourceAuthError, SourceNetworkError, SourceRateLimitError, SourceResponseError


def response(status=200, payload=None, links=None):
    result = Mock(status_code=status, ok=200 <= status < 300, text="")
    result.json.return_value = payload
    result.links = links or {}
    return result


def test_gitee_link_pagination_does_not_reuse_original_query():
    first = response(200, [{"id": 1}], {"next": {"url": "https://gitee.com/api/v5/search/repositories?page=2"}})
    second = response(200, [{"id": 2}])
    with patch("requests.request", side_effect=[first, second]) as request:
        assert GiteeClient("token").search_repositories("acme") == [{"id": 1}, {"id": 2}]
    assert request.call_args_list[1].kwargs["params"] == {"access_token": "token"}


@pytest.mark.parametrize(("status", "error"), [(401, SourceAuthError), (403, SourceAuthError), (429, SourceRateLimitError), (500, SourceNetworkError), (422, SourceResponseError)])
def test_gitee_http_errors_before_json(status, error):
    result = response(status)
    with patch("requests.request", return_value=result), pytest.raises(error):
        GiteeClient("token").get_current_user()
    result.json.assert_not_called()


def test_gitee_invalid_json():
    result = response()
    result.json.side_effect = requests.exceptions.JSONDecodeError("bad", "", 0)
    with patch("requests.request", return_value=result), pytest.raises(SourceResponseError):
        GiteeClient("token").get_current_user()
