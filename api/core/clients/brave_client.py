import requests

from core.sources.base import SourceAuthError, SourceNetworkError, SourceRateLimitError, SourceResponseError


class BraveSearchClient:
    def __init__(self, api_key: str, proxy_url: str = ""):
        # Copy/paste and encrypted storage must not turn surrounding whitespace into
        # part of the subscription token sent on the wire.
        self.api_key = api_key.strip()
        self.url = "https://api.search.brave.com/res/v1/web/search"
        self.proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    def search(self, query: str, *, count: int = 20, offset: int = 0):
        try:
            response = requests.get(
                self.url,
                headers={
                    "X-Subscription-Token": self.api_key,
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    # Brave validates this header strictly. Explicitly setting it also
                    # prevents HTTP proxies from injecting an unsupported cache policy.
                    "Cache-Control": "no-cache",
                },
                params={"q": query, "count": min(count, 20), "offset": offset},
                timeout=(5, 30),
                proxies=self.proxies,
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
            detail = self._error_detail(response)
            if response.status_code == 422 and "subscription token" in detail.lower() and "invalid" in detail.lower():
                raise SourceAuthError("Brave Search API key is invalid or unauthorized")
            suffix = f" ({detail})" if detail else ""
            raise SourceResponseError(f"Brave Search API error: HTTP {response.status_code}{suffix}")
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

    @staticmethod
    def _error_detail(response) -> str:
        """Return a short Brave validation message without exposing request secrets."""
        try:
            payload = response.json()
        except (requests.exceptions.JSONDecodeError, ValueError):
            return ""
        if not isinstance(payload, dict):
            return ""
        error = payload.get("error")
        if not isinstance(error, dict):
            return ""
        detail = str(error.get("detail") or "").strip()
        validation_errors = error.get("meta", {}).get("errors", []) if isinstance(error.get("meta"), dict) else []
        if validation_errors and isinstance(validation_errors[0], dict):
            item = validation_errors[0]
            location = ".".join(str(part) for part in item.get("loc", []))
            message = str(item.get("msg") or "").strip()
            if location and message:
                detail = f"{detail}: {location} {message}" if detail else f"{location} {message}"
        return detail[:500]
