from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from findings.models import Finding, FindingOccurrence
from scans.models import Scan


class LargeListPaginationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pagination-user")
        self.client.force_authenticate(self.user)

    def test_scans_are_paginated(self):
        Scan.objects.bulk_create(
            [Scan(user=self.user, value=f"target-{index}") for index in range(21)]
        )

        first_page = self.client.get("/scans/")
        second_page = self.client.get("/scans/?page=2")

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(first_page.data["count"], 21)
        self.assertEqual(len(first_page.data["results"]), 20)
        self.assertEqual(len(second_page.data["results"]), 1)

    def test_findings_are_paginated(self):
        scan = Scan.objects.create(user=self.user, value="target")
        findings = Finding.objects.bulk_create(
            [
                Finding(
                    scan=scan,
                    repository="owner/repository",
                    type="secret",
                    value=f"secret-{index}",
                    secret_hash=f"hash-{index}",
                    fingerprint=f"fingerprint-{index}",
                    file="config.txt",
                    email="developer@example.com",
                    commit_hash=f"commit-{index}",
                )
                for index in range(21)
            ]
        )
        FindingOccurrence.objects.bulk_create(
            [FindingOccurrence(finding=finding, scan=scan) for finding in findings]
        )

        first_page = self.client.get("/findings/")
        second_page = self.client.get("/findings/?page=2")

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(first_page.data["count"], 21)
        self.assertEqual(len(first_page.data["results"]), 20)
        self.assertEqual(len(second_page.data["results"]), 1)
