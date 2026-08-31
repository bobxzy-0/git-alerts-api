import json
import subprocess
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.detection.gitleaks import GitleaksEngine
from core.detection.base import git_clone, git_network_environment
from core.detection.registry import get_detection_engines
from core.detection.regex import CustomRegexEngine
from core.models import DetectionPattern


def test_gitleaks_normalizes_report():
    clone = Mock(stdout="")
    report = Mock(stdout=json.dumps([{
        "RuleID": "aws-access-token", "Secret": "AKIAEXAMPLE", "File": "config.env",
        "StartLine": 3, "Commit": "abc", "Email": "dev@example.com", "Description": "AWS key",
    }]))
    with patch("subprocess.run", side_effect=[clone, report]):
        finding = GitleaksEngine().scan_repository("https://example.com/acme/repo")[0]
    assert finding["type"] == "aws-access-token"
    assert finding["file"] == "config.env"
    assert finding["verified"] is False


def test_gitleaks_reports_clone_stderr_and_redacts_credentials():
    error = subprocess.CalledProcessError(
        128,
        ["git", "clone"],
        stderr="fatal: unable to access 'https://token@example.com/repo': proxy failed",
    )
    with patch("subprocess.run", side_effect=error):
        with pytest.raises(Exception) as exc_info:
            GitleaksEngine().scan_repository("https://example.com/acme/repo")

    message = str(exc_info.value)
    assert "proxy failed" in message
    assert "token" not in message


def test_git_clone_retries_and_forces_http_1_1(tmp_path):
    transient = subprocess.CalledProcessError(
        128, ["git", "clone"], stderr="GnuTLS recv error (-110)"
    )
    success = Mock(stdout="")
    with patch("core.detection.base.subprocess.run", side_effect=[transient, success]) as run, \
         patch("core.detection.base.time.sleep") as sleep:
        git_clone("https://github.com/acme/repo", tmp_path / "repo")

    assert run.call_count == 2
    assert "http.version=HTTP/1.1" in run.call_args.args[0]
    sleep.assert_called_once_with(1)


def test_trufflehog_git_environment_forces_http_1_1():
    environment = git_network_environment({"PATH": "/usr/bin"})

    assert environment["GIT_CONFIG_KEY_0"] == "http.version"
    assert environment["GIT_CONFIG_VALUE_0"] == "HTTP/1.1"


@pytest.mark.django_db
def test_registry_loads_user_custom_patterns():
    user = User.objects.create_user(username="pattern-user")
    DetectionPattern.objects.create(user=user, name="Internal host", finding_type="Internal Domain", pattern=r"\.corp\.example$")
    engines = get_detection_engines(user)
    regex_engine = next(engine for engine in engines if isinstance(engine, CustomRegexEngine))
    assert any(name == "Internal Domain" for name, _ in regex_engine.patterns)


@pytest.mark.django_db
def test_detection_pattern_api_rejects_invalid_regex():
    user = User.objects.create_user(username="pattern-api")
    client = APIClient()
    client.force_authenticate(user)
    response = client.post("/detection-patterns/", {
        "name": "broken", "finding_type": "Custom", "pattern": "[", "enabled": True,
    }, format="json")
    assert response.status_code == 400
