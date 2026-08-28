import time
import requests
from logging import getLogger

logger = getLogger(__name__)


class GitHubAuthError(Exception):
    """Raised when GitHub token is invalid or unauthorized"""

    pass


class GitHubRateLimitError(Exception):
    """Raised when GitHub rate limit is exceeded"""

    pass


class GitHubAPIError(Exception):
    """Raised for other GitHub API errors"""

    pass


class GitHubNetworkError(GitHubAPIError):
    """Raised for transport errors and temporary GitHub server failures."""


class GitHubResponseError(GitHubAPIError):
    """Raised when GitHub returns malformed or unexpected response data."""


class GitHubNotFoundError(GitHubAPIError):
    """Raised when a requested GitHub resource does not exist."""


class GitHubClient:
    """GitHub Client to fetch repositories for different scans"""

    def __init__(self, token: str, proxy_url: str = ""):
        self.token = token
        self.base_url = "https://api.github.com"
        self.proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def _sleep_until_reset(self, response):
        """Sleep until GitHub rate limit reset"""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            wait_seconds = max(0, int(retry_after))
            logger.warning(f"event=github_rate_limit_hit sleeping_seconds={wait_seconds}")
            time.sleep(wait_seconds)
            return

        reset_ts = int(response.headers.get("X-RateLimit-Reset", 0))
        now = int(time.time())
        wait_seconds = max(0, reset_ts - now)

        logger.warning(f"event=github_rate_limit_hit sleeping_seconds={wait_seconds}")
        time.sleep(wait_seconds)

    def _request(self, method: str, url: str, _retries=0, **kwargs):
        """Centralised request wrapper with logging and error handling"""
        CORE_API_MAX_RETRIES = 3
        SEARCH_API_MAX_RETRIES = 20

        logger.info(f"event=github_request_started method={method} url={url}")

        kwargs.setdefault("timeout", (5, 30))
        if self.proxies:
            kwargs.setdefault("proxies", self.proxies)

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._headers(),
                **kwargs,
            )
        except requests.RequestException as e:
            logger.error(
                f"event=github_request_error url={url} error={e}", exc_info=True
            )
            raise GitHubNetworkError(f"Network error: {e}") from e

        if response.status_code == 401:
            logger.error(f"event=github_authentication_failed url={url}")
            raise GitHubAuthError("Invalid GitHub token")

        is_rate_limited = response.status_code == 429 or (
            response.status_code == 403
            and response.headers.get("X-RateLimit-Remaining") == "0"
        )
        if is_rate_limited:
            is_search_limit = response.headers.get("X-RateLimit-Resource") == "search"
            max_retries = SEARCH_API_MAX_RETRIES if is_search_limit else CORE_API_MAX_RETRIES
            logger.warning(
                f"event=github_rate_limit_exceeded url={url} retries={_retries}"
            )
            if _retries >= max_retries:
                raise GitHubRateLimitError("GitHub API rate limit retry max reached")
            self._sleep_until_reset(response)
            return self._request(method, url, _retries=_retries + 1, **kwargs)

        # HTTP failures must be classified before any caller attempts JSON parsing.
        if response.status_code == 403:
            raise GitHubAuthError("GitHub access forbidden; token permissions may be insufficient")
        if response.status_code == 404:
            raise GitHubNotFoundError(f"GitHub resource not found: {url}")
        if 500 <= response.status_code:
            raise GitHubNetworkError(
                f"GitHub service error: HTTP {response.status_code} for {url}"
            )
        if not response.ok:
            detail = (response.text or "").strip().replace("\n", " ")[:300]
            raise GitHubResponseError(
                f"GitHub API error: HTTP {response.status_code} for {url}"
                + (f": {detail}" if detail else "")
            )

        logger.info(
            f"event=github_request_completed method={method} url={url} status={response.status_code}"
        )

        return response

    @staticmethod
    def _response_json(response):
        """Decode JSON only after HTTP status validation and normalize errors."""
        try:
            return response.json()
        except (requests.exceptions.JSONDecodeError, ValueError) as exc:
            raise GitHubResponseError(
                f"GitHub returned invalid JSON for {response.url or 'unknown URL'}"
            ) from exc

    def _get_all_pages(self, url: str, **kwargs) -> list[dict]:
        """Generic pagintor for GitHub APIs"""
        results = []
        params = kwargs.pop("params", {"per_page": 100})

        while url:
            response = self._request("GET", url=url, params=params, **kwargs)
            data = self._response_json(response)
            if not isinstance(data, list):
                raise GitHubResponseError(
                    f"Expected a list from GitHub pagination, got {type(data).__name__}"
                )
            results.extend(data)

            links = response.links
            if "next" in links:
                url = links["next"]["url"]
                # GitHub's Link URL already includes all query and page parameters.
                params = None
            else:
                url = None

        return results

    def _search_all_pages(
        self, url: str, delay_seconds: int = 0, **kwargs
    ) -> list[dict]:
        """Generic paginator for GitHub search APIs

        Args:
            url: API endpoint URL
            delay_seconds: Delay between requests to avoid rate limits (default: 0)
            **kwargs: Additional arguments passed to _request
        """
        results = []
        params = kwargs.pop("params", {"per_page": 100})

        while url:
            response = self._request("GET", url=url, params=params, **kwargs)
            data = self._response_json(response)
            if not isinstance(data, dict):
                raise GitHubResponseError(
                    f"Expected an object from GitHub search, got {type(data).__name__}"
                )

            items = data.get("items", [])
            if not isinstance(items, list):
                raise GitHubResponseError(
                    f"Expected search items to be a list, got {type(items).__name__}"
                )
            results.extend(items)

            links = response.links
            if "next" in links:
                url = links["next"]["url"]
                params = None
                # Add delay before next request if specified
                if delay_seconds > 0:
                    logger.debug(
                        f"event=github_rate_limit_delay sleeping_seconds={delay_seconds}"
                    )
                    time.sleep(delay_seconds)
            else:
                url = None

        return results

    @staticmethod
    def is_organization_repo(repo_data: dict) -> bool:
        """Check if a repository is owned by an organization"""
        try:
            if "repository" in repo_data:
                owner = repo_data["repository"].get("owner", {})
            else:
                owner = repo_data.get("owner", {})

            return owner.get("type") == "Organization"
        except (KeyError, AttributeError):
            return False

    def get_org_repos(self, org_name: str) -> list[dict]:
        """Fetches GitHub organization repositories from a given organization"""
        logger.info(f"event=github_get_org_repos_started org={org_name}")

        url = f"{self.base_url}/orgs/{org_name}/repos"
        try:
            repositories = self._get_all_pages(url=url)
        except GitHubNotFoundError:
            logger.info(f"event=github_org_not_found org={org_name}")
            repositories = []

        logger.info(
            f"event=github_get_org_repos_completed org={org_name} repo_count={len(repositories)}"
        )

        return repositories

    def get_org_members(self, org_name: str) -> list[str]:
        """Fetches GitHub organization members from a given organization"""
        logger.info(f"event=github_get_org_members_started org={org_name}")

        url = f"{self.base_url}/orgs/{org_name}/members"
        try:
            members = self._get_all_pages(url=url)
        except GitHubNotFoundError:
            logger.info(f"event=github_org_not_found org={org_name}")
            members = []
        usernames = [member["login"] for member in members]

        logger.info(
            f"event=github_org_members_completed org={org_name} members_count={len(usernames)}"
        )

        return usernames

    def get_user_repos(self, username: str) -> list[dict]:
        """Fetches all repositories for a user"""
        logger.info(f"event=github_get_user_repos_started username={username}")

        url = f"{self.base_url}/users/{username}/repos"
        try:
            repositories = self._get_all_pages(url=url)
        except GitHubNotFoundError:
            logger.info(f"event=github_user_not_found username={username}")
            repositories = []

        logger.info(
            f"event=github_get_user_repos_completed username={username} repo_count={len(repositories)}"
        )

        return repositories

    def get_org_members_repos(self, org_name: str) -> list[dict]:
        """Fetches repositories belonging to all members of an organization"""
        logger.info(f"event=github_get_org_members_repos_started org={org_name}")
        all_repositories = []
        members = self.get_org_members(org_name=org_name)

        for username in members:
            repos = self.get_user_repos(username=username)

            for repo in repos:
                all_repositories.append(repo)

        logger.info(
            f"event=github_get_org_members_repos_completed org={org_name} repo_count={len(all_repositories)}"
        )

        return all_repositories

    def get_repository(self, owner: str, repository: str) -> dict:
        """Fetch one repository using the same HTTP and JSON safety rules."""
        url = f"{self.base_url}/repos/{owner}/{repository}"
        response = self._request("GET", url)
        data = self._response_json(response)
        if not isinstance(data, dict):
            raise GitHubResponseError(
                f"Expected a repository object, got {type(data).__name__}"
            )
        return data

    def get_rate_limit(self) -> dict:
        response = self._request("GET", f"{self.base_url}/rate_limit")
        data = self._response_json(response)
        if not isinstance(data, dict):
            raise GitHubResponseError(
                f"Expected a rate limit object, got {type(data).__name__}"
            )
        return data

    def search_code(self, query: str) -> list[dict]:
        """Fetches repositories using GitHub code search for a given query"""
        logger.info(f"event=github_search_code_started query={query}")

        url = f"{self.base_url}/search/code"

        params: dict = {
            "q": query,
            "per_page": 100,
        }
        repsitories = self._search_all_pages(url=url, delay_seconds=10, params=params)

        logger.info(
            f"event=github_search_code_completed query={query} repo_count={len(repsitories)}"
        )

        return repsitories

    def search_commits(self, query: str) -> list[dict]:
        """Fetches repositories using GitHub commit search for a given query"""
        logger.info(f"event=github_search_commits_started query={query}")

        url = f"{self.base_url}/search/commits"

        params: dict = {
            "q": query,
            "per_page": 100,
        }
        repsitories = self._search_all_pages(url=url, params=params)

        logger.info(
            f"event=github_search_commits_completed query={query} repo_count={len(repsitories)}"
        )

        return repsitories

    def search_issues(self, query: str) -> list[dict]:
        """Fetches repositories using GitHub issues search for a given query"""
        logger.info(f"event=github_search_issues_started query={query}")

        url = f"{self.base_url}/search/issues"

        params: dict = {
            "q": query,
            "per_page": 100,
        }
        repsitories = self._search_all_pages(url=url, params=params)

        logger.info(
            f"event=github_search_commits_completed query={query} repo_count={len(repsitories)}"
        )

        return repsitories

    def search_repositories(self, query: str) -> list[dict]:
        """Fetches repositories using Github repository search for a given query"""
        logger.info(f"event=github_search_repositories_started query={query}")

        url = f"{self.base_url}/search/repositories"

        params: dict = {
            "q": query,
            "per_page": 100,
        }
        repsitories = self._search_all_pages(url=url, params=params)

        logger.info(
            f"event=github_search_repositories_completed query={query} repo_count={len(repsitories)}"
        )

        return repsitories

    def search_users(self, query: str) -> list[dict]:
        """Fetches user repository using GitHub user search for a given query"""
        logger.info(f"event=github_search_users_started query={query}")

        all_repositories = []
        url = f"{self.base_url}/search/users"

        params: dict = {
            "q": query,
            "per_page": 100,
        }

        users = self._search_all_pages(url=url, params=params)
        usernames = [user["login"] for user in users]

        for username in usernames:
            repos = self.get_user_repos(username=username)

            for repo in repos:
                all_repositories.append(repo)

        logger.info(f"event=github_search_users_completed query={query}")

        return all_repositories
