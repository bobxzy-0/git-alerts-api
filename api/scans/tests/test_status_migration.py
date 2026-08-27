from django.contrib.auth.models import User
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class ScanStatusMigrationTests(TransactionTestCase):
    migrate_from = [("scans", "0010_alter_scan_type")]
    migrate_to = [("scans", "0011_scan_status_model")]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        UserModel = old_apps.get_model("auth", "User")
        Scan = old_apps.get_model("scans", "Scan")
        user = UserModel.objects.create(username="migration-user")
        Scan.objects.create(
            user_id=user.pk,
            type="org_repos",
            value="empty-result",
            status="completed",
            total_repositories=1,
            total_findings=0,
        )
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        MigrationExecutor(connection).migrate(
            MigrationExecutor(connection).loader.graph.leaf_nodes()
        )
        super().tearDown()

    def test_completed_scan_without_findings_migrates_to_healthy(self):
        Scan = self.apps.get_model("scans", "Scan")
        scan = Scan.objects.get(value="empty-result")
        self.assertEqual(scan.execution_status, "SUCCESS")
        self.assertEqual(scan.monitoring_status, "HEALTHY")
        self.assertEqual(scan.result_status, "HEALTHY_NO_FINDINGS")
