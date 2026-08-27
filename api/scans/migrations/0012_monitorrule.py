import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("scans", "0011_scan_status_model"),
    ]

    operations = [
        migrations.CreateModel(
            name="MonitorRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("enabled", models.BooleanField(default=True)),
                ("source", models.CharField(choices=[("github", "GitHub"), ("gitlab", "GitLab"), ("gitee", "Gitee"), ("bitbucket", "Bitbucket"), ("codeberg", "Codeberg"), ("brave", "Brave Search")], default="github", max_length=32)),
                ("scan_type", models.CharField(choices=[("org_repos", "Organization Repositories"), ("org_users", "Organization Users"), ("search_code", "Search Code"), ("search_commits", "Search Commits"), ("search_issues", "Search Issues"), ("search_repos", "Search Repositories"), ("search_users", "Search Users")], max_length=255)),
                ("value", models.CharField(max_length=512)),
                ("interval_minutes", models.PositiveIntegerField(choices=[(15, "15 minutes"), (30, "30 minutes"), (60, "1 hour"), (120, "2 hours"), (360, "6 hours"), (720, "12 hours"), (1440, "24 hours")], default=60)),
                ("last_run_at", models.DateTimeField(blank=True, null=True)),
                ("next_run_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("is_running", models.BooleanField(db_index=True, default=False)),
                ("locked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("last_scan", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="monitor_rule_runs", to="scans.scan")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="monitor_rules", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddConstraint(
            model_name="monitorrule",
            constraint=models.UniqueConstraint(fields=("user", "name"), name="unique_monitor_rule_name_per_user"),
        ),
    ]
