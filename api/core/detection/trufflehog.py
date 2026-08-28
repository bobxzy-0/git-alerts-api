from core.clients.trufflehog_client import TruffleHogClient

from .base import BaseDetectionEngine


class TruffleHogEngine(BaseDetectionEngine):
    name = "trufflehog"

    def __init__(self, proxy_url: str = ""):
        self.client = TruffleHogClient(proxy_url)

    def scan_repository(self, repository_url, *, only_verified=True):
        return self.client.scan_repository(repository_url, only_verified=only_verified)
