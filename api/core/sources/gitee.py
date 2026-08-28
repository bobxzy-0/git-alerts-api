from urllib.parse import urlparse

from core.clients.gitee_client import GiteeClient
from scans.models import Scan, SourceType

from .base import AdapterHealth, BaseSourceAdapter, RepositoryTarget, SourceNotFoundError


class GiteeAdapter(BaseSourceAdapter):
    source = SourceType.GITEE

    def __init__(self, token: str, proxy_url: str = ""):
        self.client = GiteeClient(token, proxy_url=proxy_url)

    def health_check(self):
        self.client.get_current_user()
        return AdapterHealth(healthy=True)

    def search(self, scan_type, value, *, org_repos_only=False):
        if scan_type == Scan.ScanTypes.REPOSITORY:
            target = self.resolve(value)
            return [target] if target else []
        if scan_type == Scan.ScanTypes.ORG_REPOS:
            results = self.client.get_org_repositories(value)
        elif scan_type == Scan.ScanTypes.SEARCH_REPOS:
            results = self.client.search_repositories(value)
        else:
            raise ValueError(f"Unsupported Gitee scan type: {scan_type}")
        targets = {}
        for repository in results:
            target = self._from_repository(repository)
            if target:
                targets[target.url] = target
        return list(targets.values())

    def resolve(self, value):
        parsed = urlparse(value)
        if parsed.netloc.lower() not in {"gitee.com", "www.gitee.com"}:
            return None
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 2:
            return None
        owner, name = parts[0], parts[1].removesuffix(".git")
        try:
            repository = self.client.get_repository(owner, name)
        except SourceNotFoundError:
            return None
        return self._from_repository(repository)

    def _from_repository(self, repository):
        url = repository.get("html_url")
        full_name = repository.get("full_name", "")
        if not url or "/" not in full_name:
            return None
        owner, name = full_name.split("/", 1)
        return RepositoryTarget(
            source=self.source, url=url, owner=owner, name=name,
            metadata={"private": repository.get("private"), "default_branch": repository.get("default_branch")},
        )
