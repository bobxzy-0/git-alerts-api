from urllib.parse import quote

import requests

from core.sources.base import (
    SourceAuthError, SourceNetworkError, SourceNotFoundError,
    SourceRateLimitError, SourceResponseError,
)


class GiteeClient:
    """Gitee API v5 client for supported discovery operations."""

    def __init__(self, token: str, base_url: str = "https://gitee.com/api/v5", proxy_url: str = ""):
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    def _request(self, method: str, url: str, **kwargs):
        params = kwargs.pop("params", None) or {}
        params.setdefault("access_token", self.token)
        kwargs.setdefault("timeout", (5, 30))
        if self.proxies:
            kwargs.setdefault("proxies", self.proxies)
        try:
            response = requests.request(method, url, params=params, **kwargs)
        except requests.RequestException as exc:
            raise SourceNetworkError(f"Gitee network error: {exc}") from exc
        if response.status_code in {401, 403}:
            raise SourceAuthError("Gitee token is invalid or lacks required permissions")
        if response.status_code == 404:
            raise SourceNotFoundError(f"Gitee resource not found: {url}")
        if response.status_code == 429:
            raise SourceRateLimitError("Gitee API rate limit exceeded")
        if response.status_code >= 500:
            raise SourceNetworkError(f"Gitee service error: HTTP {response.status_code}")
        if not response.ok:
            raise SourceResponseError(f"Gitee API error: HTTP {response.status_code}")
        return response

    @staticmethod
    def _json(response):
        try:
            return response.json()
        except (requests.exceptions.JSONDecodeError, ValueError) as exc:
            raise SourceResponseError("Gitee returned invalid JSON") from exc

    def _get_pages(self, path: str, params=None):
        url = f"{self.base_url}{path}"
        page_params = {"per_page": 100, **(params or {})}
        results = []
        while url:
            response = self._request("GET", url, params=page_params)
            data = self._json(response)
            if not isinstance(data, list):
                raise SourceResponseError(
                    f"Expected a list from Gitee pagination, got {type(data).__name__}"
                )
            results.extend(data)
            next_link = response.links.get("next", {}).get("url")
            if next_link:
                url = next_link
                page_params = None
            else:
                url = None
        return results

    def get_current_user(self):
        response = self._request("GET", f"{self.base_url}/user")
        data = self._json(response)
        if not isinstance(data, dict):
            raise SourceResponseError("Expected a user object from Gitee")
        return data

    def get_org_repositories(self, organization: str):
        return self._get_pages(f"/orgs/{quote(organization, safe='')}/repos")

    def search_repositories(self, query: str):
        return self._get_pages("/search/repositories", {"q": query})

    def get_repository(self, owner: str, name: str):
        response = self._request(
            "GET", f"{self.base_url}/repos/{quote(owner, safe='')}/{quote(name, safe='')}"
        )
        data = self._json(response)
        if not isinstance(data, dict):
            raise SourceResponseError("Expected a repository object from Gitee")
        return data
