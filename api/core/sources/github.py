from urllib.parse import urlparse

from core.clients.github_client import (
    GitHubAuthError, GitHubClient, GitHubNetworkError, GitHubNotFoundError,
    GitHubRateLimitError, GitHubResponseError,
)
from scans.models import Scan, SourceType

from .base import (
    AdapterHealth, BaseSourceAdapter, RepositoryTarget, SourceAuthError,
    SourceNetworkError, SourceNotFoundError, SourceRateLimitError,
    SourceResponseError,
)


class GitHubAdapter(BaseSourceAdapter):
    source = SourceType.GITHUB

    def __init__(self, token: str):
        self.client = GitHubClient(token=token)

    def health_check(self) -> AdapterHealth:
        data = self._call(self.client.get_rate_limit)
        core = data.get("resources", {}).get("core", {})
        return AdapterHealth(
            healthy=True,
            rate_limit_remaining=core.get("remaining"),
        )

    def search(
        self, scan_type: str, value: str, *, org_repos_only: bool = False
    ) -> list[RepositoryTarget]:
        if scan_type == Scan.ScanTypes.REPOSITORY:
            target = self.resolve(value)
            return [target] if target else []
        handlers = {
            Scan.ScanTypes.ORG_REPOS: self.client.get_org_repos,
            Scan.ScanTypes.ORG_USERS: self.client.get_org_members_repos,
            Scan.ScanTypes.SEARCH_CODE: self.client.search_code,
            Scan.ScanTypes.SEARCH_COMMITS: self.client.search_commits,
            Scan.ScanTypes.SEARCH_ISSUES: self.client.search_issues,
            Scan.ScanTypes.SEARCH_REPOS: self.client.search_repositories,
            Scan.ScanTypes.SEARCH_USERS: self.client.search_users,
        }
        try:
            raw_results = self._call(handlers[scan_type], value)
        except KeyError as exc:
            raise ValueError(f"Unsupported GitHub scan type: {scan_type}") from exc

        targets: dict[str, RepositoryTarget] = {}
        for raw in raw_results:
            target = self._normalize(scan_type, raw)
            if target is None:
                continue
            if org_repos_only and not self._is_organization_target(target, raw):
                continue
            targets[target.url] = target
        return list(targets.values())

    def resolve(self, value: str) -> RepositoryTarget | None:
        parsed = urlparse(value)
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            return None
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 2:
            return None
        owner, name = parts[0], parts[1].removesuffix(".git")
        try:
            raw = self._call(self.client.get_repository, owner, name)
        except SourceNotFoundError:
            return None
        return self._from_repository(raw)

    @staticmethod
    def _call(operation, *args, **kwargs):
        try:
            return operation(*args, **kwargs)
        except GitHubAuthError as exc:
            raise SourceAuthError(str(exc)) from exc
        except GitHubRateLimitError as exc:
            raise SourceRateLimitError(str(exc)) from exc
        except GitHubNetworkError as exc:
            raise SourceNetworkError(str(exc)) from exc
        except GitHubNotFoundError as exc:
            raise SourceNotFoundError(str(exc)) from exc
        except GitHubResponseError as exc:
            raise SourceResponseError(str(exc)) from exc

    def _is_organization_target(self, target: RepositoryTarget, raw: dict) -> bool:
        owner_type = target.metadata.get("owner_type")
        if owner_type is None and "repository_url" in raw:
            repository = self._call(self.client.get_repository, target.owner, target.name)
            owner_type = repository.get("owner", {}).get("type")
        return owner_type == "Organization"

    def _normalize(self, scan_type: str, raw: dict) -> RepositoryTarget | None:
        if scan_type in {Scan.ScanTypes.SEARCH_CODE, Scan.ScanTypes.SEARCH_COMMITS}:
            repository = raw.get("repository", {})
            return self._from_repository(repository)
        if scan_type == Scan.ScanTypes.SEARCH_ISSUES:
            repository_url = raw.get("repository_url", "")
            parts = repository_url.rstrip("/").split("/")
            if len(parts) < 2:
                return None
            owner, name = parts[-2], parts[-1]
            return RepositoryTarget(
                source=self.source,
                url=f"https://github.com/{owner}/{name}",
                owner=owner,
                name=name,
            )
        return self._from_repository(raw)

    def _from_repository(self, repository: dict) -> RepositoryTarget | None:
        url = repository.get("html_url")
        full_name = repository.get("full_name", "")
        if not url:
            return None
        if "/" in full_name:
            owner, name = full_name.split("/", 1)
        else:
            parts = url.rstrip("/").split("/")
            if len(parts) < 2:
                return None
            owner, name = parts[-2], parts[-1]
        return RepositoryTarget(
            source=self.source,
            url=url,
            owner=owner,
            name=name,
            metadata={"owner_type": repository.get("owner", {}).get("type")},
        )
