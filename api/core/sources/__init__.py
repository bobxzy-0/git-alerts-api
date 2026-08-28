from .base import (
    AdapterHealth,
    BaseSourceAdapter,
    RepositoryTarget,
    SourceAuthError,
    SourceError,
    SourceNetworkError,
    SourceNotFoundError,
    SourceRateLimitError,
    SourceResponseError,
)


def get_source_adapter(source: str, *, token: str, proxy_url: str = ""):
    # Keep registry loading lazy so HTTP clients can import source exceptions
    # without creating a package import cycle.
    from .registry import get_source_adapter as resolve_adapter

    return resolve_adapter(source, token=token, proxy_url=proxy_url)

__all__ = [
    "AdapterHealth", "BaseSourceAdapter", "RepositoryTarget", "SourceError",
    "SourceAuthError", "SourceRateLimitError", "SourceNetworkError",
    "SourceResponseError", "SourceNotFoundError", "get_source_adapter",
]
