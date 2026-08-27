from django.db import migrations, models


def migrate_scan_statuses(apps, schema_editor):
    Scan = apps.get_model("scans", "Scan")
    for scan in Scan.objects.all().iterator():
        old_status = scan.execution_status
        if old_status == "queued":
            scan.execution_status = "QUEUED"
        elif old_status == "in_progress":
            scan.execution_status = "RUNNING"
        elif old_status == "completed":
            scan.execution_status = "SUCCESS"
            if scan.total_repositories == 0:
                scan.monitoring_status = "HEALTHY"
                scan.result_status = "HEALTHY_TARGET_ABSENT"
            elif scan.total_findings == 0:
                scan.monitoring_status = "HEALTHY"
                scan.result_status = "HEALTHY_NO_FINDINGS"
            else:
                scan.monitoring_status = "WARNING"
                scan.result_status = "FINDINGS_MEDIUM"
        else:
            scan.execution_status = "FAILED"
            scan.monitoring_status = "UNKNOWN"
            scan.result_status = "FAILED_INTERNAL"
            scan.error_code = "LEGACY_SCAN_FAILED"
            scan.error_message = "Migrated from legacy failed status"
        scan.save(update_fields=[
            "execution_status", "monitoring_status", "result_status",
            "error_code", "error_message",
        ])


class Migration(migrations.Migration):
    dependencies = [("scans", "0010_alter_scan_type")]

    operations = [
        migrations.RenameField(
            model_name="scan",
            old_name="status",
            new_name="execution_status",
        ),
        migrations.AddField(
            model_name="scan",
            name="monitoring_status",
            field=models.CharField(default="UNKNOWN", max_length=32),
        ),
        migrations.AddField(
            model_name="scan",
            name="result_status",
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name="scan",
            name="error_code",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="scan",
            name="error_message",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="scan",
            name="started_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(migrate_scan_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="scan",
            name="execution_status",
            field=models.CharField(
                choices=[
                    ("QUEUED", "Queued"), ("RUNNING", "Running"),
                    ("SUCCESS", "Success"), ("DEGRADED", "Degraded"),
                    ("FAILED", "Failed"),
                ],
                default="QUEUED",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="scan",
            name="monitoring_status",
            field=models.CharField(
                choices=[
                    ("HEALTHY", "Healthy"), ("WARNING", "Warning"),
                    ("CRITICAL", "Critical"), ("UNKNOWN", "Unknown"),
                ],
                default="UNKNOWN",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="scan",
            name="result_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("HEALTHY_NO_FINDINGS", "Healthy - No Findings"),
                    ("HEALTHY_TARGET_ABSENT", "Healthy - Target Absent"),
                    ("FINDINGS_LOW", "Low Risk Findings"),
                    ("FINDINGS_MEDIUM", "Medium Risk Findings"),
                    ("FINDINGS_HIGH", "High Risk Findings"),
                    ("FINDINGS_CRITICAL", "Critical Risk Findings"),
                    ("DEGRADED_RATE_LIMIT", "Degraded - Rate Limited"),
                    ("FAILED_AUTH", "Failed - Authentication"),
                    ("FAILED_NETWORK", "Failed - Network"),
                    ("FAILED_INTERNAL", "Failed - Internal"),
                ],
                max_length=32,
                null=True,
            ),
        ),
    ]
