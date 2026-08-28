from scans.models import SourceType

from .base import BaseSourceAdapter
from .github import GitHubAdapter
from .gitlab import GitLabAdapter
from .gitee import GiteeAdapter
from .you import YouSearchAdapter


def get_source_adapter(source: str, *, token: str, proxy_url: str = "") -> BaseSourceAdapter:
    if source == SourceType.GITHUB:
        return GitHubAdapter(token=token, proxy_url=proxy_url)
    if source == SourceType.GITLAB:
        return GitLabAdapter(token=token, proxy_url=proxy_url)
    if source == SourceType.GITEE:
        return GiteeAdapter(token=token, proxy_url=proxy_url)
    if source == SourceType.YOU:
        return YouSearchAdapter(token=token, proxy_url=proxy_url)
    raise ValueError(f"Source adapter is not enabled: {source}")
