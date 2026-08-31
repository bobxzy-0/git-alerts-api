import re
import subprocess
import tempfile
from pathlib import Path

from .base import BaseDetectionEngine, DetectionEngineError, git_clone, process_error_message


DEFAULT_PATTERNS = [
    ("Private Key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("AWS Key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Database Connection", re.compile(r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?)://[^\s'\"]+", re.I)),
    ("Password", re.compile(r"(?i)(?:password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]")),
]


class CustomRegexEngine(BaseDetectionEngine):
    name = "custom_regex"

    def __init__(self, patterns=None, proxy_url: str = ""):
        self.patterns = DEFAULT_PATTERNS + list(patterns or [])
        self.proxy_url = proxy_url

    def scan_repository(self, repository_url, *, only_verified=True):
        findings = []
        with tempfile.TemporaryDirectory(prefix="gitalerts-regex-") as directory:
            try:
                git_clone(
                    repository_url, directory, proxy_url=self.proxy_url, depth=1
                )
            except (subprocess.SubprocessError, DetectionEngineError) as exc:
                raise DetectionEngineError(
                    f"Regex engine clone failed: {process_error_message(exc)}"
                ) from exc
            root = Path(directory)
            for path in root.rglob("*"):
                if not path.is_file() or ".git" in path.parts or path.stat().st_size > 2_000_000:
                    continue
                try:
                    lines = path.read_text(errors="strict").splitlines()
                except (UnicodeError, OSError):
                    continue
                for line_number, line in enumerate(lines, 1):
                    for finding_type, pattern in self.patterns:
                        for match in pattern.finditer(line):
                            findings.append({"repository": repository_url, "commit": "", "file": str(path.relative_to(root)), "line": line_number, "author": "", "type": finding_type, "description": "Matched custom sensitive pattern", "value": match.group(0), "verified": False})
        return findings
