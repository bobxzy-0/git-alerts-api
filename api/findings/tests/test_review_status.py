from django.contrib.auth.models import User
from django.test import TestCase

from findings.models import Finding
from findings.serializers import FindingSerializer
from scans.models import Scan


class FindingReviewStatusTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="review-user", password="test")
        self.scan = Scan.objects.create(user=self.user, type=Scan.ScanTypes.REPOSITORY, value="https://github.com/acme/demo")
        self.finding = Finding.objects.create(
            scan=self.scan, last_scan=self.scan, source="github", repository="acme/demo",
            type="AWS Access Key", value="AKIA...", secret_hash="a" * 64, fingerprint="b" * 64,
            file="config.yml", email="dev@example.com", commit_hash="deadbeef",
        )

    def test_not_an_issue_maps_to_false_positive(self):
        updated = FindingSerializer(self.finding, data={"review_status": Finding.ReviewStatus.NOT_AN_ISSUE}, partial=True).save()
        self.assertEqual(updated.review_status, Finding.ReviewStatus.NOT_AN_ISSUE)
        self.assertEqual(updated.lifecycle_status, Finding.LifecycleStatus.FALSE_POSITIVE)

    def test_ignored_maps_to_ignored_lifecycle(self):
        updated = FindingSerializer(self.finding, data={"review_status": Finding.ReviewStatus.IGNORED}, partial=True).save()
        self.assertEqual(updated.lifecycle_status, Finding.LifecycleStatus.IGNORED)
