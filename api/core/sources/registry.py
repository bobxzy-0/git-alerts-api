from scans.models import SourceType

from .base import BaseSourceAdapter
from .github import GitHubAdapter
from .gitlab import GitLabAdapter
from .gitee import GiteeAdapter
from .brave import BraveSearchAdapter


def get_source_adapter(source: str, *, token: str) -> BaseSourceAdapter:
    if source == SourceType.GITHUB:
        return GitHubAdapter(token=token)
    if source == SourceType.GITLAB:
        return GitLabAdapter(token=token)
    if source == SourceType.GITEE:
        return GiteeAdapter(token=token)
    if source == SourceType.BRAVE:
        return BraveSearchAdapter(token=token)
    raise ValueError(f"Source adapter is not enabled: {source}")
