from unittest.mock import Mock, call, patch

import pytest

from core.clients.github_client import (
    GitHubAuthError,
    GitHubClient,
    GitHubNetworkError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubResponseError,
)


def response(*, status=200, data=None, links=None, headers=None, text=""):
    result = Mock()
    result.status_code = status
    result.ok = 200 <= status < 400
    result.headers = headers or {}
    result.links = links or {}
    result.text = text
    result.url = "https://api.github.com/test"
    result.json.return_value = data
    return result


def test_regular_pagination_clears_params_for_link_next_url():
    client = GitHubClient("token")
    first = response(
        data=[{"id": 1}],
        links={"next": {"url": "https://api.github.com/items?page=2&per_page=100"}},
    )
    second = response(data=[{"id": 2}])

    with patch.object(client, "_request", side_effect=[first, second]) as request:
        results = client._get_all_pages(
            "https://api.github.com/items", params={"per_page": 100}
        )

    assert results == [{"id": 1}, {"id": 2}]
    assert request.call_args_list == [
        call("GET", url="https://api.github.com/items", params={"per_page": 100}),
        call(
            "GET",
            url="https://api.github.com/items?page=2&per_page=100",
            params=None,
        ),
    ]


def test_search_pagination_clears_params_for_link_next_url():
    client = GitHubClient("token")
    first = response(
        data={"items": [{"id": 1}]},
        links={"next": {"url": "https://api.github.com/search/code?q=x&page=2"}},
    )
    second = response(data={"items": []})

    with patch.object(client, "_request", side_effect=[first, second]) as request:
        results = client._search_all_pages(
            "https://api.github.com/search/code", params={"q": "x", "per_page": 100}
        )

    assert results == [{"id": 1}]
    assert request.call_args_list[1].kwargs["params"] is None


def test_empty_search_result_is_valid_success():
    client = GitHubClient("token")
    with patch.object(
        client, "_request", return_value=response(data={"total_count": 0, "items": []})
    ):
        assert client.search_repositories("no-match") == []


def test_dictionary_cannot_be_extended_as_regular_page_results():
    client = GitHubClient("token")
    with (
        patch.object(client, "_request", return_value=response(data={"message": "error"})),
        pytest.raises(GitHubResponseError, match="Expected a list"),
    ):
        client._get_all_pages("https://api.github.com/items")


def test_search_items_must_be_a_list():
    client = GitHubClient("token")
    with (
        patch.object(client, "_request", return_value=response(data={"items": {"id": 1}})),
        pytest.raises(GitHubResponseError, match="search items"),
    ):
        client._search_all_pages("https://api.github.com/search/code")


@pytest.mark.parametrize(
    ("status", "headers", "exception"),
    [
        (403, {}, GitHubAuthError),
        (404, {}, GitHubNotFoundError),
        (500, {}, GitHubNetworkError),
    ],
)
def test_http_errors_are_raised_before_json(status, headers, exception):
    client = GitHubClient("token")
    error_response = response(status=status, data={"message": "error"}, headers=headers)

    with (
        patch("core.clients.github_client.requests.request", return_value=error_response),
        pytest.raises(exception),
    ):
        client._request("GET", "https://api.github.com/test")

    error_response.json.assert_not_called()


def test_429_is_classified_as_rate_limit():
    client = GitHubClient("token")
    limited = response(status=429, headers={"Retry-After": "0"})

    with (
        patch("core.clients.github_client.requests.request", return_value=limited) as request,
        patch("core.clients.github_client.time.sleep"),
        pytest.raises(GitHubRateLimitError),
    ):
        client._request("GET", "https://api.github.com/test")

    assert request.call_count == 4
    limited.json.assert_not_called()


def test_invalid_json_is_normalized():
    client = GitHubClient("token")
    invalid = response(data=None)
    invalid.json.side_effect = ValueError("invalid json")

    with (
        patch.object(client, "_request", return_value=invalid),
        pytest.raises(GitHubResponseError, match="invalid JSON"),
    ):
        client._get_all_pages("https://api.github.com/items")


def test_missing_organization_is_a_healthy_empty_target():
    client = GitHubClient("token")
    with patch.object(client, "_get_all_pages", side_effect=GitHubNotFoundError("missing")):
        assert client.get_org_repos("missing-org") == []
