import requests

from core.sources.base import SourceAuthError, SourceNetworkError, SourceRateLimitError, SourceResponseError


class BraveSearchClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.search.brave.com/res/v1/web/search"

    def search(self, query: str, *, count: int = 20, offset: int = 0):
        try:
            response = requests.get(
                self.url,
                headers={"X-Subscription-Token": self.api_key, "Accept": "application/json"},
                params={"q": query, "count": min(count, 20), "offset": offset},
                timeout=(5, 30),
            )
        except requests.RequestException as exc:
            raise SourceNetworkError(f"Brave Search network error: {exc}") from exc
        if response.status_code in {401, 403}:
            raise SourceAuthError("Brave Search API key is invalid or unauthorized")
        if response.status_code == 429:
            raise SourceRateLimitError("Brave Search API rate limit exceeded")
        if response.status_code >= 500:
            raise SourceNetworkError(f"Brave Search service error: HTTP {response.status_code}")
        if not response.ok:
            raise SourceResponseError(f"Brave Search API error: HTTP {response.status_code}")
        try:
            data = response.json()
        except (requests.exceptions.JSONDecodeError, ValueError) as exc:
            raise SourceResponseError("Brave Search returned invalid JSON") from exc
        if not isinstance(data, dict):
            raise SourceResponseError("Expected an object from Brave Search")
        results = data.get("web", {}).get("results", [])
        if not isinstance(results, list):
            raise SourceResponseError("Expected Brave web results to be a list")
        return results, response.headers
