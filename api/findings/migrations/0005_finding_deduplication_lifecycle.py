import hashlib

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def migrate_findings(apps, schema_editor):
    Finding = apps.get_model("findings", "Finding")
    FindingOccurrence = apps.get_model("findings", "FindingOccurrence")

    for finding in Finding.objects.select_related("scan").order_by("id").iterator():
        raw_value = finding.value or ""
        secret_hash = hashlib.sha256(raw_value.encode()).hexdigest()
        source = getattr(finding.scan, "source", "github") if finding.scan_id else "github"
        fingerprint_input = "\0".join([
            source,
            finding.repository or "",
            finding.file or "",
            finding.type or "",
            secret_hash,
        ])
        fingerprint = hashlib.sha256(fingerprint_input.encode()).hexdigest()
        existing = Finding.objects.filter(fingerprint=fingerprint).exclude(pk=finding.pk).first()
        if existing:
            if finding.scan_id:
                FindingOccurrence.objects.get_or_create(
                    finding_id=existing.pk, scan_id=finding.scan_id
                )
            existing.occurrence_count = FindingOccurrence.objects.filter(
                finding_id=existing.pk
            ).count()
            existing.last_seen_at = max(existing.last_seen_at, finding.created_at)
            existing.save(update_fields=["occurrence_count", "last_seen_at"])
            finding.delete()
            continue

        masked = "********" if len(raw_value) <= 8 else f"{raw_value[:4]}…{raw_value[-4:]}"
        finding.source = source
        finding.secret_hash = secret_hash
        finding.fingerprint = fingerprint
        finding.value = masked
        finding.last_scan_id = finding.scan_id
        finding.first_seen_at = finding.created_at
        finding.last_seen_at = finding.created_at
        finding.lifecycle_status = "ACTIVE"
        finding.save(update_fields=[
            "source", "secret_hash", "fingerprint", "value", "last_scan",
            "first_seen_at", "last_seen_at", "lifecycle_status",
        ])
        if finding.scan_id:
            FindingOccurrence.objects.get_or_create(
                finding_id=finding.pk, scan_id=finding.scan_id
            )


class Migration(migrations.Migration):
    dependencies = [
        ("findings", "0004_finding_validated"),
        ("scans", "0013_scan_source"),
    ]

    operations = [
        migrations.AlterField(
            model_name="finding",
            name="scan",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="findings", to="scans.scan"),
        ),
        migrations.AddField(model_name="finding", name="source", field=models.CharField(default="github", max_length=32)),
        migrations.AddField(model_name="finding", name="secret_hash", field=models.CharField(blank=True, default="", max_length=64)),
        migrations.AddField(model_name="finding", name="fingerprint", field=models.CharField(blank=True, default="", max_length=64)),
        migrations.AddField(model_name="finding", name="lifecycle_status", field=models.CharField(choices=[("NEW", "New"), ("ACTIVE", "Active"), ("ACKNOWLEDGED", "Acknowledged"), ("RESOLVED", "Resolved"), ("REOPENED", "Reopened"), ("IGNORED", "Ignored"), ("FALSE_POSITIVE", "False Positive")], default="NEW", max_length=32)),
        migrations.AddField(model_name="finding", name="severity", field=models.CharField(choices=[("CRITICAL", "Critical"), ("HIGH", "High"), ("MEDIUM", "Medium"), ("LOW", "Low"), ("INFO", "Info")], default="MEDIUM", max_length=16)),
        migrations.AddField(model_name="finding", name="risk_score", field=models.PositiveSmallIntegerField(default=50)),
        migrations.AddField(model_name="finding", name="first_seen_at", field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AddField(model_name="finding", name="last_seen_at", field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AddField(model_name="finding", name="occurrence_count", field=models.PositiveIntegerField(default=1)),
        migrations.AddField(model_name="finding", name="last_scan", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="latest_findings", to="scans.scan")),
        migrations.CreateModel(
            name="FindingOccurrence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("observed_at", models.DateTimeField(auto_now_add=True)),
                ("finding", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="occurrences", to="findings.finding")),
                ("scan", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="finding_occurrences", to="scans.scan")),
            ],
        ),
        migrations.AddConstraint(
            model_name="findingoccurrence",
            constraint=models.UniqueConstraint(fields=("finding", "scan"), name="unique_finding_occurrence_per_scan"),
        ),
        migrations.RunPython(migrate_findings, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="finding",
            name="secret_hash",
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name="finding",
            name="fingerprint",
            field=models.CharField(max_length=64, unique=True),
        ),
    ]
