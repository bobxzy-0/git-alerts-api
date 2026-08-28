from urllib.parse import quote

import requests

from core.sources.base import (
    SourceAuthError,
    SourceNetworkError,
    SourceNotFoundError,
    SourceRateLimitError,
    SourceResponseError,
)


class GitLabClient:
    """Small GitLab REST v4 client with strict HTTP and payload handling."""

    def __init__(self, token: str, base_url: str = "https://gitlab.com/api/v4", proxy_url: str = ""):
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    def _headers(self):
        return {"PRIVATE-TOKEN": self.token, "Accept": "application/json"}

    def _request(self, method: str, url: str, **kwargs):
        kwargs.setdefault("timeout", (5, 30))
        if self.proxies:
            kwargs.setdefault("proxies", self.proxies)
        try:
            response = requests.request(method, url, headers=self._headers(), **kwargs)
        except requests.RequestException as exc:
            raise SourceNetworkError(f"GitLab network error: {exc}") from exc

        if response.status_code == 401:
            raise SourceAuthError("GitLab token is invalid or expired")
        if response.status_code == 403:
            raise SourceAuthError("GitLab token lacks required permissions")
        if response.status_code == 404:
            raise SourceNotFoundError(f"GitLab resource not found: {url}")
        if response.status_code == 429:
            raise SourceRateLimitError("GitLab API rate limit exceeded")
        if response.status_code >= 500:
            raise SourceNetworkError(
                f"GitLab service error: HTTP {response.status_code} for {url}"
            )
        if not response.ok:
            detail = (response.text or "").strip().replace("\n", " ")[:300]
            raise SourceResponseError(
                f"GitLab API error: HTTP {response.status_code} for {url}"
                + (f": {detail}" if detail else "")
            )
        return response

    @staticmethod
    def _json(response):
        try:
            return response.json()
        except (requests.exceptions.JSONDecodeError, ValueError) as exc:
            raise SourceResponseError("GitLab returned invalid JSON") from exc

    def _get_pages(self, path: str, params=None) -> list[dict]:
        url = f"{self.base_url}{path}"
        page_params = {"per_page": 100, **(params or {})}
        results = []
        while url:
            response = self._request("GET", url, params=page_params)
            data = self._json(response)
            if not isinstance(data, list):
                raise SourceResponseError(
                    f"Expected a list from GitLab pagination, got {type(data).__name__}"
                )
            results.extend(data)
            next_page = response.headers.get("X-Next-Page")
            if next_page:
                page_params = {**page_params, "page": next_page}
            else:
                url = None
        return results

    def get_current_user(self) -> dict:
        response = self._request("GET", f"{self.base_url}/user")
        data = self._json(response)
        if not isinstance(data, dict):
            raise SourceResponseError("Expected a user object from GitLab")
        return data

    def get_group_projects(self, group: str) -> list[dict]:
        return self._get_pages(
            f"/groups/{quote(group, safe='')}/projects",
            {"include_subgroups": "true", "with_shared": "false"},
        )

    def search_projects(self, query: str) -> list[dict]:
        return self._get_pages("/projects", {"search": query, "simple": "true"})

    def get_project(self, namespace: str, name: str) -> dict:
        project_id = quote(f"{namespace}/{name}", safe="")
        response = self._request("GET", f"{self.base_url}/projects/{project_id}")
        data = self._json(response)
        if not isinstance(data, dict):
            raise SourceResponseError("Expected a project object from GitLab")
        return data
