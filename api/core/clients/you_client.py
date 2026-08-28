import requests

from core.sources.base import SourceAuthError, SourceNetworkError, SourceRateLimitError, SourceResponseError


class YouSearchClient:
    url = "https://ydc-index.io/v1/search"

    def __init__(self, api_key: str, proxy_url: str = ""):
        self.api_key = api_key.strip()
        self.proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    def search(self, query: str, *, count: int = 10, offset: int = 0):
        try:
            response = requests.post(
                self.url,
                headers={"X-API-Key": self.api_key, "Content-Type": "application/json", "Accept": "application/json"},
                json={"query": query, "count": min(max(count, 1), 100), "offset": offset},
                timeout=(5, 30),
                proxies=self.proxies,
            )
        except requests.RequestException as exc:
            raise SourceNetworkError(f"You.com Search network error: {exc}") from exc
        if response.status_code in {401, 403}:
            raise SourceAuthError("You.com API key is invalid or unauthorized")
        if response.status_code in {402, 429}:
            raise SourceRateLimitError("You.com API credits are exhausted or rate limited")
        if response.status_code >= 500:
            raise SourceNetworkError(f"You.com Search service error: HTTP {response.status_code}")
        if not response.ok:
            raise SourceResponseError(f"You.com Search API error: HTTP {response.status_code}")
        try:
            data = response.json()
        except (requests.exceptions.JSONDecodeError, ValueError) as exc:
            raise SourceResponseError("You.com Search returned invalid JSON") from exc
        if not isinstance(data, dict) or not isinstance(data.get("results", {}), dict):
            raise SourceResponseError("Expected a You.com Search result object")
        results = data["results"]
        combined = []
        for section in ("web", "news"):
            items = results.get(section, [])
            if not isinstance(items, list):
                raise SourceResponseError(f"Expected You.com {section} results to be a list")
            combined.extend(items)
        return combined, response.headers
