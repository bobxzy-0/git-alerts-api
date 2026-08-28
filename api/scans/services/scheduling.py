from datetime import datetime, timedelta

from croniter import croniter
from django.utils import timezone


def next_occurrence(rule, after):
    """Return the next timezone-aware occurrence for a monitor rule."""
    if rule.schedule_kind == rule.ScheduleKinds.INTERVAL:
        if rule.pk is None and rule.last_run_at is None:
            return after
        return after + timedelta(minutes=rule.interval_minutes)

    local_after = timezone.localtime(after)
    if rule.schedule_kind == rule.ScheduleKinds.CRON:
        return croniter(rule.cron_expression, local_after).get_next(datetime)

    candidate = datetime.combine(
        local_after.date(), rule.schedule_time, tzinfo=local_after.tzinfo
    )
    if rule.schedule_kind == rule.ScheduleKinds.DAILY:
        if candidate <= local_after:
            candidate += timedelta(days=1)
        return candidate

    weekdays = set(rule.schedule_weekdays)
    for offset in range(8):
        current = candidate + timedelta(days=offset)
        if current.weekday() in weekdays and current > local_after:
            return current
    raise ValueError("A weekly schedule requires at least one weekday")
