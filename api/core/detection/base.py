from abc import ABC, abstractmethod


class DetectionEngineError(Exception):
    pass


class BaseDetectionEngine(ABC):
    name: str

    @abstractmethod
    def scan_repository(self, repository_url: str, *, only_verified: bool = True) -> list[dict]:
        raise NotImplementedError
