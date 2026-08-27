from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0006_systemsettings_org_repos_only"),
    ]

    operations = [
        migrations.CreateModel(
            name="SourceHealth",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(max_length=32)),
                ("status", models.CharField(choices=[("HEALTHY", "Healthy"), ("WARNING", "Warning"), ("CRITICAL", "Critical"), ("UNKNOWN", "Unknown")], default="UNKNOWN", max_length=16)),
                ("last_checked_at", models.DateTimeField(blank=True, null=True)),
                ("last_success_at", models.DateTimeField(blank=True, null=True)),
                ("last_failure_at", models.DateTimeField(blank=True, null=True)),
                ("result_count", models.PositiveIntegerField(default=0)),
                ("new_findings", models.PositiveIntegerField(default=0)),
                ("rate_limit_remaining", models.IntegerField(blank=True, null=True)),
                ("error_code", models.CharField(blank=True, default="", max_length=64)),
                ("error_message", models.TextField(blank=True, default="")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="source_health", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["source"]},
        ),
        migrations.AddConstraint(
            model_name="sourcehealth",
            constraint=models.UniqueConstraint(fields=("user", "source"), name="unique_source_health_per_user"),
        ),
    ]
