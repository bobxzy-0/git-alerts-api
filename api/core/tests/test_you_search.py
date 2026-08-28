from unittest.mock import Mock, patch

import pytest

from core.clients.you_client import YouSearchClient
from core.sources import SourceAuthError, SourceRateLimitError, SourceResponseError
from core.sources.you import YouSearchAdapter
from scans.models import Scan


def response(status=200, payload=None):
    result = Mock(status_code=status, ok=200 <= status < 300, headers={})
    result.json.return_value = payload
    return result


def test_you_uses_official_post_endpoint_and_api_key_header():
    result = response(200, {"results": {"web": [], "news": []}})
    with patch("requests.post", return_value=result) as request:
        YouSearchClient("  you-key-value\n").search("acme", count=5)
    assert request.call_args.args[0] == "https://ydc-index.io/v1/search"
    assert request.call_args.kwargs["headers"]["X-API-Key"] == "you-key-value"
    assert request.call_args.kwargs["json"] == {"query": "acme", "count": 5, "offset": 0}


@pytest.mark.parametrize(("status", "error"), [(401, SourceAuthError), (403, SourceAuthError), (402, SourceRateLimitError), (429, SourceRateLimitError)])
def test_you_classifies_api_failures(status, error):
    with patch("requests.post", return_value=response(status)), pytest.raises(error):
        YouSearchClient("key").search("acme")


def test_you_rejects_invalid_result_shape():
    with patch("requests.post", return_value=response(200, {"results": []})), pytest.raises(SourceResponseError):
        YouSearchClient("key").search("acme")


def test_you_adapter_resolves_and_deduplicates_repository_urls():
    adapter = YouSearchAdapter("key")
    adapter.client = Mock()
    adapter.client.search.return_value = ([
        {"url": "https://github.com/acme/api/blob/main/a.py"},
        {"url": "https://github.com/acme/api/issues/1"},
        {"url": "https://codeberg.org/acme/platform/src/branch/main"},
    ], {})
    targets = adapter.search(Scan.ScanTypes.SEARCH_REPOS, "acme")
    assert {(item.source, item.owner, item.name) for item in targets} == {
        ("github", "acme", "api"), ("codeberg", "acme", "platform")
    }
