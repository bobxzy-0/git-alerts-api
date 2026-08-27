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


@pytest.mark.parametrize(("status", "error"), [(401, SourceAuthError), (403, SourceAuthError), (429, SourceRateLimitError), (400, SourceResponseError)])
def test_brave_http_failures_are_classified_before_json(status, error):
    result = response(status)
    with patch("requests.get", return_value=result), pytest.raises(error):
        BraveSearchClient("key").search("acme")
    result.json.assert_not_called()


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
