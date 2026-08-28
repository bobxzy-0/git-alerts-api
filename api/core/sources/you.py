from urllib.parse import urlparse

from core.clients.you_client import YouSearchClient
from scans.models import Scan, SourceType

from .base import AdapterHealth, RepositoryTarget
from .search_engine import SearchEngineAdapter


class YouSearchAdapter(SearchEngineAdapter):
    source = SourceType.YOU

    def __init__(self, token: str, proxy_url: str = ""):
        self.client = YouSearchClient(token, proxy_url=proxy_url)

    def health_check(self):
        self.client.search("site:github.com", count=1)
        return AdapterHealth(True)

    def search(self, scan_type, value, *, org_repos_only=False):
        if scan_type != Scan.ScanTypes.SEARCH_REPOS:
            raise ValueError("You.com Search supports search_repos only")
        results, _ = self.client.search(value)
        targets = {}
        for result in results:
            if not isinstance(result, dict):
                continue
            target = self.resolve(result.get("url", ""))
            if target:
                targets[f"{target.source}:{target.owner}/{target.name}"] = target
        return list(targets.values())

    def resolve(self, value):
        parsed = urlparse(value)
        host = parsed.netloc.lower().removeprefix("www.")
        platform = self.supported_hosts.get(host)
        parts = [part for part in parsed.path.split("/") if part]
        if not platform or len(parts) < 2:
            return None
        if platform == "gitlab" and "-" in parts:
            parts = parts[:parts.index("-")]
        if platform == "gitlab":
            owner, name = "/".join(parts[:-1]), parts[-1].removesuffix(".git")
        else:
            owner, name = parts[0], parts[1].removesuffix(".git")
        return RepositoryTarget(platform, f"https://{host}/{owner}/{name}", owner, name, {"discovered_by": "you"})
