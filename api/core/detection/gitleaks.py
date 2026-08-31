import json
import subprocess
import tempfile

from .base import BaseDetectionEngine, DetectionEngineError, git_clone, process_error_message


class GitleaksEngine(BaseDetectionEngine):
    name = "gitleaks"

    def __init__(self, proxy_url: str = ""):
        self.proxy_url = proxy_url

    def scan_repository(self, repository_url, *, only_verified=True):
        with tempfile.TemporaryDirectory(prefix="gitalerts-gitleaks-") as directory:
            try:
                git_clone(
                    repository_url, directory, proxy_url=self.proxy_url, mirror=True
                )
                result = subprocess.run(
                    ["gitleaks", "git", directory, "--report-format", "json", "--report-path", "-", "--exit-code", "0"],
                    check=True, timeout=600, capture_output=True, text=True,
                )
                payload = json.loads(result.stdout or "[]")
            except (subprocess.SubprocessError, json.JSONDecodeError, DetectionEngineError) as exc:
                raise DetectionEngineError(
                    f"Gitleaks scan failed: {process_error_message(exc)}"
                ) from exc
        if not isinstance(payload, list):
            raise DetectionEngineError("Gitleaks returned a non-list report")
        return [{
            "repository": repository_url,
            "commit": item.get("Commit"), "file": item.get("File"),
            "line": item.get("StartLine"), "author": item.get("Email"),
            "type": item.get("RuleID") or "Gitleaks Secret",
            "description": item.get("Description") or "Detected by Gitleaks",
            "value": item.get("Secret") or item.get("Match") or "",
            "verified": False,
        } for item in payload]
