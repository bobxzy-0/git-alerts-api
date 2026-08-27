from .base import BaseSourceAdapter


class SearchEngineAdapter(BaseSourceAdapter):
    """Marker base for official search-engine API adapters."""

    supported_hosts = {
        "github.com": "github", "gitlab.com": "gitlab", "gitee.com": "gitee",
        "bitbucket.org": "bitbucket", "codeberg.org": "codeberg",
    }
