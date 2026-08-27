from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class SourceError(Exception):
    """Base exception for platform-independent source failures."""


class SourceAuthError(SourceError):
    pass


class SourceRateLimitError(SourceError):
    pass


class SourceNetworkError(SourceError):
    pass


class SourceResponseError(SourceError):
    pass


class SourceNotFoundError(SourceError):
    pass


@dataclass(frozen=True)
class RepositoryTarget:
    source: str
    url: str
    owner: str
    name: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AdapterHealth:
    healthy: bool
    rate_limit_remaining: int | None = None
    detail: str = ""


class BaseSourceAdapter(ABC):
    source: str

    @abstractmethod
    def health_check(self) -> AdapterHealth:
        raise NotImplementedError

    @abstractmethod
    def search(
        self, scan_type: str, value: str, *, org_repos_only: bool = False
    ) -> list[RepositoryTarget]:
        raise NotImplementedError

    @abstractmethod
    def resolve(self, value: str) -> RepositoryTarget | None:
        raise NotImplementedError
