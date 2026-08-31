from abc import ABC, abstractmethod
import re
import shutil
import subprocess
import time
from pathlib import Path


class DetectionEngineError(Exception):
    pass


def process_error_message(exc: BaseException, limit: int = 1000) -> str:
    """Return useful subprocess output without leaking URL credentials."""
    details = getattr(exc, "stderr", None) or getattr(exc, "stdout", None) or str(exc)
    details = str(details).strip() or exc.__class__.__name__
    details = re.sub(r"(https?://)[^/@\s]+@", r"\1***@", details)
    return details[-limit:]


def git_clone(
    repository_url: str,
    target: str | Path,
    *,
    proxy_url: str = "",
    mirror: bool = False,
    depth: int | None = None,
    attempts: int = 2,
) -> None:
    """Clone with conservative GitHub TLS settings and transient-error retries."""
    target = Path(target)
    command = [
        "git",
        "-c", "http.version=HTTP/1.1",
        "-c", "http.lowSpeedLimit=1000",
        "-c", "http.lowSpeedTime=60",
    ]
    if proxy_url:
        command.extend(["-c", f"http.proxy={proxy_url}"])
    command.extend(["clone", "--quiet"])
    if mirror:
        command.append("--mirror")
    if depth is not None:
        command.extend(["--depth", str(depth)])
    command.extend([repository_url, str(target)])

    last_error = None
    for attempt in range(1, attempts + 1):
        if target.exists():
            shutil.rmtree(target)
        try:
            subprocess.run(
                command, check=True, timeout=300, capture_output=True, text=True
            )
            return
        except subprocess.SubprocessError as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(attempt)
    raise DetectionEngineError(
        f"Git clone failed after {attempts} attempts: {process_error_message(last_error)}"
    ) from last_error


def git_network_environment(environment: dict[str, str]) -> dict[str, str]:
    """Make Git subprocesses use HTTP/1.1 to avoid unstable HTTP/2 TLS sessions."""
    result = environment.copy()
    result.update({
        "GIT_CONFIG_COUNT": "3",
        "GIT_CONFIG_KEY_0": "http.version",
        "GIT_CONFIG_VALUE_0": "HTTP/1.1",
        "GIT_CONFIG_KEY_1": "http.lowSpeedLimit",
        "GIT_CONFIG_VALUE_1": "1000",
        "GIT_CONFIG_KEY_2": "http.lowSpeedTime",
        "GIT_CONFIG_VALUE_2": "60",
    })
    return result


class BaseDetectionEngine(ABC):
    name: str

    @abstractmethod
    def scan_repository(self, repository_url: str, *, only_verified: bool = True) -> list[dict]:
        raise NotImplementedError
