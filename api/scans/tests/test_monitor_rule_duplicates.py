from django.contrib.auth.models import User
from django.test import TestCase

from scans.models import MonitorRule, Scan


class MonitorRuleDuplicateNameTests(TestCase):
    def test_same_user_can_have_duplicate_plan_names(self):
        user = User.objects.create_user(username="plan-user", password="test")
        common = {
            "user": user,
            "name": "Daily repository scan",
            "source": "github",
            "scan_type": Scan.ScanTypes.SEARCH_REPOS,
            "value": "acme",
        }
        MonitorRule.objects.create(**common)
        MonitorRule.objects.create(**common, value="example")
        self.assertEqual(MonitorRule.objects.filter(user=user, name="Daily repository scan").count(), 2)
