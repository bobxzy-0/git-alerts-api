from unittest.mock import Mock, patch

import pytest

from core.clients.brave_client import BraveSearchClient
from core.sources import SourceAuthError, SourceRateLimitError, SourceResponseError
from core.sources.brave import BraveSearchAdapter
from scans.models import Scan


def response(status=200, payload=None):
    result = Mock(status_code=status, ok=200 <= status < 300, headers={})
    result.json.return_value = payload
    return result


@pytest.mark.parametrize(("status", "error"), [(401, SourceAuthError), (403, SourceAuthError), (429, SourceRateLimitError)])
def test_brave_http_failures_are_classified_before_json(status, error):
    result = response(status)
    with patch("requests.get", return_value=result), pytest.raises(error):
        BraveSearchClient("key").search("acme")
    result.json.assert_not_called()


def test_brave_sends_proxy_safe_cache_headers():
    result = response(200, {"web": {"results": []}})
    with patch("requests.get", return_value=result) as request:
        BraveSearchClient("key").search("site:github.com", count=1)

    headers = request.call_args.kwargs["headers"]
    assert headers["Cache-Control"] == "no-cache"
    assert headers["Accept-Encoding"] == "gzip"


def test_brave_strips_token_whitespace_before_sending():
    result = response(200, {"web": {"results": []}})
    with patch("requests.get", return_value=result) as request:
        BraveSearchClient("  valid-key\n").search("acme")
    assert request.call_args.kwargs["headers"]["X-Subscription-Token"] == "valid-key"


def test_brave_422_includes_validation_detail():
    result = response(422, {
        "error": {
            "detail": "Unable to validate request parameter(s)",
            "meta": {"errors": [{"loc": ["header", "cache-control"], "msg": "Input should be 'no-cache'"}]},
        }
    })
    with patch("requests.get", return_value=result), pytest.raises(SourceResponseError, match="cache-control"):
        BraveSearchClient("key").search("acme")


def test_brave_422_invalid_subscription_token_is_auth_failure():
    result = response(422, {"error": {"detail": "The provided subscription token is invalid."}})
    with patch("requests.get", return_value=result), pytest.raises(SourceAuthError, match="API key is invalid"):
        BraveSearchClient("bad-key").search("acme")


def test_brave_adapter_extracts_supported_repositories_and_deduplicates():
    adapter = BraveSearchAdapter("key")
    adapter.client = Mock()
    adapter.client.search.return_value = ([
        {"url": "https://github.com/acme/api/blob/main/a.py"},
        {"url": "https://github.com/acme/api/issues/1"},
        {"url": "https://gitlab.com/acme/platform/-/tree/main"},
        {"url": "https://example.com/not-a-repository"},
    ], {})
    targets = adapter.search(Scan.ScanTypes.SEARCH_REPOS, "acme secret")
    assert {(target.source, target.owner, target.name) for target in targets} == {
        ("github", "acme", "api"), ("gitlab", "acme", "platform")
    }


def test_brave_rejects_unsupported_search_type():
    with pytest.raises(ValueError, match="Unsupported"):
        BraveSearchAdapter("key").search(Scan.ScanTypes.SEARCH_CODE, "secret")
