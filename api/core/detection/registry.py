import re

from core.models import DetectionPattern

from .gitleaks import GitleaksEngine
from .regex import CustomRegexEngine
from .trufflehog import TruffleHogEngine


def get_detection_engines(user=None, proxy_url: str = ""):
    patterns = []
    if user is not None:
        for item in DetectionPattern.objects.filter(user=user, enabled=True):
            patterns.append((item.finding_type, re.compile(item.pattern, re.I if item.ignore_case else 0)))
    return [TruffleHogEngine(proxy_url), GitleaksEngine(proxy_url), CustomRegexEngine(patterns, proxy_url)]
