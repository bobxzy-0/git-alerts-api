from django.db import migrations, models


def reschedule_enabled_rules(apps, schema_editor):
    """Recalculate existing wall-clock schedules in the new explicit time zone."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    from croniter import croniter
    from django.utils import timezone

    MonitorRule = apps.get_model("scans", "MonitorRule")
    now = timezone.now()
    for rule in MonitorRule.objects.filter(enabled=True, is_running=False).iterator():
        if rule.schedule_kind == "INTERVAL":
            if rule.next_run_at is None:
                rule.next_run_at = now
        else:
            local_now = now.astimezone(ZoneInfo(rule.timezone))
            if rule.schedule_kind == "CRON":
                rule.next_run_at = croniter(rule.cron_expression, local_now).get_next(datetime)
            else:
                candidate = datetime.combine(local_now.date(), rule.schedule_time, tzinfo=local_now.tzinfo)
                if rule.schedule_kind == "DAILY":
                    if candidate <= local_now:
                        candidate += timedelta(days=1)
                    rule.next_run_at = candidate
                else:
                    weekdays = set(rule.schedule_weekdays)
                    rule.next_run_at = next(
                        current for offset in range(8)
                        if (current := candidate + timedelta(days=offset)).weekday() in weekdays
                        and current > local_now
                    )
        rule.save(update_fields=["next_run_at"])


class Migration(migrations.Migration):
    dependencies = [("scans", "0018_scan_monitor_rule_scan_trigger_type")]

    operations = [
        migrations.AddField(
            model_name="monitorrule",
            name="timezone",
            field=models.CharField(default="Asia/Shanghai", max_length=64),
        ),
        migrations.RunPython(reschedule_enabled_rules, migrations.RunPython.noop),
    ]
