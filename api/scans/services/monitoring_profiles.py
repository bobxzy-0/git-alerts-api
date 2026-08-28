from scans.models import MonitorRule, Scan, SourceType


def sync_profile_rules(profile):
    """Replace generated rules deterministically while preserving manual rules."""
    profile.rules.filter(auto_generated=True).delete()
    specifications = []
    for value in profile.github_orgs:
        specifications.append((SourceType.GITHUB, Scan.ScanTypes.ORG_REPOS, value, "GitHub org"))
    for value in profile.gitlab_groups:
        specifications.append((SourceType.GITLAB, Scan.ScanTypes.ORG_REPOS, value, "GitLab group"))
    search_values = [profile.company_name] if profile.company_name else []
    for field in ("domains", "email_domains", "brands", "product_names", "internal_projects", "internal_domains", "custom_keywords"):
        search_values.extend(getattr(profile, field))
    for value in search_values:
        specifications.append((SourceType.BRAVE, Scan.ScanTypes.SEARCH_REPOS, value, "Search"))
    seen = set()
    for source, scan_type, value, label in specifications:
        normalized = str(value).strip()
        key = (source, scan_type, normalized.casefold())
        if not normalized or key in seen:
            continue
        seen.add(key)
        MonitorRule.objects.create(
            user=profile.user, profile=profile, auto_generated=True,
            name=f"Profile {profile.pk}: {label} {normalized}"[:255],
            enabled=profile.enabled, source=source, scan_type=scan_type,
            value=normalized, interval_minutes=profile.interval_minutes,
            schedule_kind=profile.schedule_kind,
            schedule_time=profile.schedule_time,
            schedule_weekdays=profile.schedule_weekdays,
            cron_expression=profile.cron_expression,
        )
