import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { monitorRulesApi, scansApi } from '@/services/api';
import type { MonitorRule, ScanType, SourceType } from '@/types';

const intervals = [15, 30, 60, 120, 360, 720, 1440] as const;

const SCAN_TYPES: { value: ScanType; label: string; description: string }[] = [
  {
    value: 'org_repos',
    label: 'Organization Repositories',
    description: 'Scan all repositories in a GitHub organization',
  },
  {
    value: 'org_users',
    label: 'Organization Users',
    description: 'Scan repositories of all members in an organization',
  },
  {
    value: 'search_code',
    label: 'Search Code',
    description: 'Scan repositories from GitHub code search results',
  },
  {
    value: 'search_commits',
    label: 'Search Commits',
    description: 'Scan repositories from GitHub commit search results',
  },
  {
    value: 'search_issues',
    label: 'Search Issues',
    description: 'Scan repositories from GitHub issue/PR search results',
  },
  {
    value: 'search_repos',
    label: 'Search Repositories',
    description: 'Scan repositories from GitHub repository search',
  },
  {
    value: 'search_users',
    label: 'Search Users',
    description: 'Scan repositories from GitHub user search results',
  },
];

export const NewScan: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [scanType, setScanType] = useState<ScanType>('org_repos');
  const [source, setSource] = useState<SourceType>('github');
  const [query, setQuery] = useState('');
  const [executionMode, setExecutionMode] = useState<'once' | 'schedule'>('once');
  const [ruleName, setRuleName] = useState('');
  const [scheduleKind, setScheduleKind] = useState<MonitorRule['schedule_kind']>('INTERVAL');
  const [intervalMinutes, setIntervalMinutes] = useState<MonitorRule['interval_minutes']>(60);
  const [scheduleTime, setScheduleTime] = useState('09:00');
  const [weekdays, setWeekdays] = useState<number[]>([0]);
  const [cronExpression, setCronExpression] = useState('0 9 * * 1-5');

  const createScanMutation = useMutation({
    mutationFn: scansApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] });
      navigate('/scans?tab=history');
    },
  });

  const createScheduleMutation = useMutation({
    mutationFn: monitorRulesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitor-rules'] });
      navigate('/scans?tab=monitors');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (executionMode === 'once') {
      createScanMutation.mutate({ type: scanType, value: query, source });
    } else {
      createScheduleMutation.mutate({
        name: ruleName, enabled: true, source, scan_type: scanType, value: query,
        interval_minutes: intervalMinutes, schedule_kind: scheduleKind,
        schedule_time: scheduleTime, schedule_weekdays: weekdays,
        cron_expression: cronExpression,
      });
    }
  };

  const selectedType = SCAN_TYPES.find((t) => t.value === scanType);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Create New Scan</h1>
        <p className="text-muted-foreground mt-2">
          Configure a new security scan for a connected source
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="rounded-lg border bg-card p-6">
          <label className="mb-3 block text-sm font-medium">执行方式</label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className={`cursor-pointer rounded-lg border p-4 ${executionMode === 'once' ? 'border-primary bg-primary/5' : ''}`}><input className="mr-2" type="radio" checked={executionMode === 'once'} onChange={() => setExecutionMode('once')}/><strong>仅执行一次</strong><p className="ml-6 mt-1 text-xs text-muted-foreground">立即创建 Scan 并加入执行队列</p></label>
            <label className={`cursor-pointer rounded-lg border p-4 ${executionMode === 'schedule' ? 'border-primary bg-primary/5' : ''}`}><input className="mr-2" type="radio" checked={executionMode === 'schedule'} onChange={() => setExecutionMode('schedule')}/><strong>定时执行</strong><p className="ml-6 mt-1 text-xs text-muted-foreground">按计划持续生成 Scan 记录</p></label>
          </div>
        </div>
        {/* Scan Type Selection */}
        <div className="bg-card border border-border rounded-lg p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Source</label>
            <select value={source} onChange={(e) => {
              const next = e.target.value as SourceType;
              setSource(next);
              if (next !== 'github' && !['org_repos', 'search_repos'].includes(scanType)) setScanType('org_repos');
              if (next === 'brave') setScanType('search_repos');
            }} className="w-full px-3 py-2 bg-background border border-input rounded-md">
              <option value="github">GitHub</option>
              <option value="gitlab">GitLab</option>
              <option value="gitee">Gitee</option>
              <option value="brave">Brave Search</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Scan Type
            </label>
            <select
              value={scanType}
              onChange={(e) => setScanType(e.target.value as ScanType)}
              className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              required
            >
              {SCAN_TYPES.filter((type) => source === 'github' || (source === 'brave' ? type.value === 'search_repos' : ['org_repos', 'search_repos'].includes(type.value))).map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
            {selectedType && (
              <p className="text-sm text-muted-foreground mt-2">
                {selectedType.description}
              </p>
            )}
          </div>

          {/* Query Input */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Query
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={getQueryPlaceholder(scanType)}
              className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              required
            />
            <p className="text-sm text-muted-foreground mt-2">
              {getQueryHelp(scanType)}
            </p>
          </div>
        </div>

        {executionMode === 'schedule' && <div className="space-y-4 rounded-lg border bg-card p-6">
          <h2 className="font-semibold">定时计划</h2>
          <div><label className="mb-2 block text-sm font-medium">计划名称</label><input required className="w-full rounded-md border bg-background px-3 py-2" placeholder="例如：公司域名每日监控" value={ruleName} onChange={e => setRuleName(e.target.value)}/></div>
          <div className="grid gap-3 sm:grid-cols-2"><select className="rounded-md border bg-background px-3 py-2" value={scheduleKind} onChange={e => setScheduleKind(e.target.value as MonitorRule['schedule_kind'])}><option value="INTERVAL">固定间隔</option><option value="DAILY">每天指定时间</option><option value="WEEKLY">每周指定时间</option><option value="CRON">高级 Cron</option></select>
          {scheduleKind === 'INTERVAL' && <select className="rounded-md border bg-background px-3 py-2" value={intervalMinutes} onChange={e => setIntervalMinutes(Number(e.target.value) as MonitorRule['interval_minutes'])}>{intervals.map(value => <option key={value} value={value}>{value < 60 ? `${value} 分钟` : `${value / 60} 小时`}</option>)}</select>}
          {(scheduleKind === 'DAILY' || scheduleKind === 'WEEKLY') && <input aria-label="执行时间" type="time" required className="rounded-md border bg-background px-3 py-2" value={scheduleTime} onChange={e => setScheduleTime(e.target.value)}/>}</div>
          {scheduleKind === 'WEEKLY' && <div className="flex flex-wrap gap-2">{['一','二','三','四','五','六','日'].map((label, day) => <label key={day} className={`cursor-pointer rounded-md border px-3 py-2 text-sm ${weekdays.includes(day) ? 'border-primary bg-primary/10' : ''}`}><input type="checkbox" className="mr-2" checked={weekdays.includes(day)} onChange={() => setWeekdays(weekdays.includes(day) ? weekdays.filter(value => value !== day) : [...weekdays, day])}/>周{label}</label>)}</div>}
          {scheduleKind === 'CRON' && <div><input required pattern="\\S+\\s+\\S+\\s+\\S+\\s+\\S+\\s+\\S+" className="w-full rounded-md border bg-background px-3 py-2 font-mono" value={cronExpression} onChange={e => setCronExpression(e.target.value)}/><p className="mt-1 text-xs text-muted-foreground">五段 Cron：分 时 日 月 周，例如 0 9 * * 1-5</p></div>}
        </div>}

        {/* Error Display */}
        {(createScanMutation.isError || createScheduleMutation.isError) && (
          <div className="p-4 bg-destructive/10 border border-destructive rounded-lg">
            <p className="text-sm font-semibold text-destructive mb-1">
              Failed to create scan
            </p>
            <p className="text-sm text-destructive">
              {(() => {
                const error = (createScanMutation.error || createScheduleMutation.error) as { response?: { data?: string | Record<string, unknown> } };
                if (error?.response?.data) {
                  // Handle validation errors
                  const data = error.response.data;
                  if (typeof data === 'string') return data;
                  if (Array.isArray(data.non_field_errors)) return data.non_field_errors[0] as string;
                  if (typeof data.detail === 'string') return data.detail;
                  // Return first error message from any field
                  const firstError = Object.values(data)[0];
                  if (Array.isArray(firstError)) return firstError[0];
                  if (typeof firstError === 'string') return firstError;
                }
                return 'Please check your input and try again.';
              })()}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={createScanMutation.isPending || createScheduleMutation.isPending}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {(createScanMutation.isPending || createScheduleMutation.isPending) ? 'Creating...' : executionMode === 'once' ? 'Create Scan' : 'Create Schedule'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/scans?tab=history')}
            className="px-6 py-2 border border-border rounded-lg font-medium hover:bg-accent transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

function getQueryPlaceholder(scanType: ScanType): string {
  switch (scanType) {
    case 'org_repos':
    case 'org_users':
      return 'e.g., microsoft';
    case 'search_code':
      return 'e.g., AWS_SECRET_KEY';
    case 'search_commits':
      return 'e.g., password OR secret';
    case 'search_issues':
      return 'e.g., exposed credentials';
    case 'search_repos':
      return 'e.g., security scanner';
    case 'search_users':
      return 'e.g., john-doe';
    default:
      return '';
  }
}

function getQueryHelp(scanType: ScanType): string {
  switch (scanType) {
    case 'org_repos':
      return 'Enter the GitHub organization name';
    case 'org_users':
      return 'Enter the GitHub organization name to scan all member repositories';
    case 'search_code':
      return 'Enter code search query (searches GitHub code)';
    case 'search_commits':
      return 'Enter commit search query (searches GitHub commits)';
    case 'search_issues':
      return 'Enter issue/PR search query (searches GitHub issues and pull requests)';
    case 'search_repos':
      return 'Enter repository search query (searches GitHub repositories)';
    case 'search_users':
      return 'Enter user search query (searches GitHub users)';
    default:
      return '';
  }
}
