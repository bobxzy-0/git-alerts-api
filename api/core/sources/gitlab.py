from urllib.parse import urlparse

from core.clients.gitlab_client import GitLabClient
from scans.models import Scan, SourceType

from .base import AdapterHealth, BaseSourceAdapter, RepositoryTarget, SourceNotFoundError


class GitLabAdapter(BaseSourceAdapter):
    source = SourceType.GITLAB

    def __init__(self, token: str, proxy_url: str = ""):
        self.client = GitLabClient(token=token, proxy_url=proxy_url)

    def health_check(self) -> AdapterHealth:
        self.client.get_current_user()
        return AdapterHealth(healthy=True)

    def search(self, scan_type, value, *, org_repos_only=False):
        if scan_type == Scan.ScanTypes.REPOSITORY:
            target = self.resolve(value)
            return [target] if target else []
        if scan_type == Scan.ScanTypes.ORG_REPOS:
            raw_results = self.client.get_group_projects(value)
        elif scan_type == Scan.ScanTypes.SEARCH_REPOS:
            raw_results = self.client.search_projects(value)
        else:
            raise ValueError(f"Unsupported GitLab scan type: {scan_type}")

        targets = {}
        for project in raw_results:
            target = self._from_project(project)
            if target:
                targets[target.url] = target
        return list(targets.values())

    def resolve(self, value: str) -> RepositoryTarget | None:
        parsed = urlparse(value)
        if parsed.netloc.lower() not in {"gitlab.com", "www.gitlab.com"}:
            return None
        parts = [part for part in parsed.path.split("/") if part]
        if "-" in parts:
            parts = parts[:parts.index("-")]
        if len(parts) < 2:
            return None
        namespace, name = "/".join(parts[:-1]), parts[-1].removesuffix(".git")
        try:
            project = self.client.get_project(namespace, name)
        except SourceNotFoundError:
            return None
        return self._from_project(project)

    def _from_project(self, project: dict) -> RepositoryTarget | None:
        url = project.get("web_url")
        full_path = project.get("path_with_namespace", "")
        if not url or "/" not in full_path:
            return None
        namespace, name = full_path.rsplit("/", 1)
        return RepositoryTarget(
            source=self.source,
            url=url,
            owner=namespace,
            name=name,
            metadata={
                "visibility": project.get("visibility"),
                "default_branch": project.get("default_branch"),
            },
        )
