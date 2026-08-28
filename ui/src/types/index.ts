// API Response Types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Auth Types
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface TokenResponse {
  access: string;
  refresh: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
}

// Scan Types
export type ScanType =
  | 'org_repos'
  | 'org_users'
  | 'search_code'
  | 'search_commits'
  | 'search_issues'
  | 'search_repos'
  | 'search_users';
export type SourceType = 'github' | 'gitlab' | 'gitee' | 'bitbucket' | 'codeberg' | 'brave';

export type ExecutionStatus = 'QUEUED' | 'RUNNING' | 'SUCCESS' | 'DEGRADED' | 'FAILED';
export type MonitoringStatus = 'HEALTHY' | 'WARNING' | 'CRITICAL' | 'UNKNOWN';
export type ResultStatus =
  | 'HEALTHY_NO_FINDINGS'
  | 'HEALTHY_TARGET_ABSENT'
  | 'FINDINGS_LOW'
  | 'FINDINGS_MEDIUM'
  | 'FINDINGS_HIGH'
  | 'FINDINGS_CRITICAL'
  | 'DEGRADED_RATE_LIMIT'
  | 'FAILED_AUTH'
  | 'FAILED_NETWORK'
  | 'FAILED_INTERNAL';

export interface Scan {
  id: number;
  user: string; // username, not user id
  type: ScanType;
  source: SourceType;
  trigger_type: 'MANUAL' | 'SCHEDULED' | 'DISCOVERY' | 'REPOSITORY_QUEUE';
  monitor_rule: number | null;
  value: string;
  execution_status: ExecutionStatus;
  monitoring_status: MonitoringStatus;
  result_status: ResultStatus | null;
  error_code: string;
  error_message: string;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  total_repositories: number;
  total_findings: number;
  ignored_repositories: number;
  ignored_findings: number;
  scanned_repositories: number;
}

export interface CreateScanRequest {
  type: ScanType;
  value: string;
  source?: SourceType;
}

// Finding Types
export interface Finding {
  id: number;
  scan: number | null;
  last_scan: number | null;
  source: string;
  repository: string;
  type: string;
  value: string;
  secret_hash: string;
  fingerprint: string;
  description: string;
  file: string;
  line: number | null;
  email: string;
  commit_hash: string;
  commit_url: string | null;
  validated: boolean;
  lifecycle_status: 'NEW' | 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED' | 'REOPENED' | 'IGNORED' | 'FALSE_POSITIVE';
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  risk_score: number;
  first_seen_at: string;
  last_seen_at: string;
  occurrence_count: number;
  created_at: string;
  updated_at: string;
}

// Ignore Types
export interface IgnoreFindingType {
  id: number;
  type: string;
  created_at: string;
}

export interface IgnoreFindingDomain {
  id: number;
  domain: string;
  created_at: string;
}

export interface CreateIgnoreTypeRequest {
  type: string;
}

export interface CreateIgnoreDomainRequest {
  domain: string;
}

// Integration Types
export type IntegrationType = 'github' | 'gitlab' | 'gitee' | 'brave' | 'slack';
export type IntegrationStatus = 'connected' | 'disconnected' | 'pending' | 'failed';

export interface UserIntegration {
  id: number;
  user: string;
  provider: IntegrationType;
  status: IntegrationStatus;
  last_validated_at: string | null;
  error_message: string;
  created_at: string;
  updated_at: string;
}

export interface CreateIntegrationRequest {
  provider: IntegrationType;
  token: string;
}

// System Settings Types
export interface SystemSettings {
  id: number;
  skip_recent_days: number;
  verified_only: boolean;
  org_repos_only: boolean;
  updated_at: string;
}

export interface UpdateSystemSettingsRequest {
  skip_recent_days?: number;
  verified_only?: boolean;
  org_repos_only?: boolean;
}

export interface SourceHealth {
  id: number; source: string; status: MonitoringStatus;
  last_checked_at: string | null; last_success_at: string | null; last_failure_at: string | null;
  result_count: number; new_findings: number; rate_limit_remaining: number | null;
  error_code: string; error_message: string;
}

export interface MonitorRule {
  id: number; name: string; enabled: boolean; source: string; scan_type: ScanType; value: string;
  profile: number | null; auto_generated: boolean;
  interval_minutes: 15 | 30 | 60 | 120 | 360 | 720 | 1440;
  schedule_kind: 'INTERVAL' | 'DAILY' | 'WEEKLY' | 'CRON'; schedule_time: string;
  schedule_weekdays: number[]; cron_expression: string;
  last_run_at: string | null; next_run_at: string | null; is_running: boolean; last_scan: number | null;
}

export interface DashboardSummary {
  overall_health: MonitoringStatus; source_health: SourceHealth[];
  severity_counts: Record<Finding['severity'], number>;
  new_findings: number; resolved_findings: number;
  recent_scans: Scan[]; recent_findings: Finding[];
  scan_trend: Array<{ date: string; count: number }>;
}

export interface NotificationChannel {
  id: number; name: string; channel_type: 'email' | 'webhook'; target: string; enabled: boolean;
  created_at: string; updated_at: string;
}

export interface MonitoringProfile {
  id: number; name: string; enabled: boolean; company_name: string;
  domains: string[]; email_domains: string[]; brands: string[]; product_names: string[];
  internal_projects: string[]; internal_domains: string[]; github_orgs: string[];
  gitlab_groups: string[]; custom_keywords: string[];
  interval_minutes: MonitorRule['interval_minutes']; generated_rule_count: number;
  schedule_kind: MonitorRule['schedule_kind']; schedule_time: string;
  schedule_weekdays: number[]; cron_expression: string;
}

export type ScanRepositoryStatus = 'DISCOVERED' | 'EXCLUDED' | 'SKIPPED_RECENT' | 'QUEUED' | 'SCANNING' | 'COMPLETED' | 'DEGRADED' | 'FAILED';

export interface ScanRepository {
  id: number; scan: number; source: SourceType; repository_url: string;
  normalized_url: string; owner: string; repository: string;
  status: ScanRepositoryStatus; error_message: string; findings_count: number;
  excluded_repository: number | null; is_permanently_excluded: boolean;
  created_at: string; updated_at: string;
}

export interface ExcludedRepository {
  id: number; source: SourceType; repository_url: string; normalized_url: string;
  owner: string; repository: string; reason: string; enabled: boolean;
  created_at: string; updated_at: string;
}
