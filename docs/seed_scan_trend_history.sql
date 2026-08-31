-- Seed synthetic historical Scan records so the Dashboard Scan Trend is populated.
-- PostgreSQL / Django table names assume the default app_label naming used by this project.
-- Safe to run multiple times: rows are tagged with the __trend_seed__ prefix.
-- Review and delete the seeded rows when real scan history is available.

INSERT INTO scans_scan (
    user_id, type, value, source, trigger_type,
    execution_status, monitoring_status, result_status, error_code,
    total_repositories, total_findings, ignored_repositories,
    ignored_findings, scanned_repositories,
    created_at, updated_at, started_at, completed_at
)
SELECT
    u.id,
    'search_repos',
    '__trend_seed__-' || gs::date,
    'you',
    'SCHEDULED',
    'SUCCESS',
    'HEALTHY',
    'HEALTHY_NO_FINDINGS',
    '',
    0, 0, 0, 0, 0,
    gs + make_interval(hours => ((u.id + EXTRACT(day FROM gs)::int) % 10)),
    gs + make_interval(hours => ((u.id + EXTRACT(day FROM gs)::int) % 10)),
    gs + make_interval(hours => ((u.id + EXTRACT(day FROM gs)::int) % 10)),
    gs + make_interval(hours => ((u.id + EXTRACT(day FROM gs)::int) % 10), mins => 1)
FROM auth_user u
CROSS JOIN generate_series(
    CURRENT_DATE - INTERVAL '29 days',
    CURRENT_DATE,
    INTERVAL '1 day'
) AS gs
WHERE NOT EXISTS (
    SELECT 1
    FROM scans_scan s
    WHERE s.user_id = u.id
      AND s.value = '__trend_seed__-' || gs::date
);

-- Optional cleanup:
-- DELETE FROM scans_scan WHERE value LIKE '__trend_seed__-%';
