from abc import ABC, abstractmethod
import re


class DetectionEngineError(Exception):
    pass


def process_error_message(exc: BaseException, limit: int = 1000) -> str:
    """Return useful subprocess output without leaking URL credentials."""
    details = getattr(exc, "stderr", None) or getattr(exc, "stdout", None) or str(exc)
    details = str(details).strip() or exc.__class__.__name__
    details = re.sub(r"(https?://)[^/@\s]+@", r"\1***@", details)
    return details[-limit:]


class BaseDetectionEngine(ABC):
    name: str

    @abstractmethod
    def scan_repository(self, repository_url: str, *, only_verified: bool = True) -> list[dict]:
        raise NotImplementedError
