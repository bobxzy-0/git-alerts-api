import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { monitorRulesApi } from '@/services/api';
import type { MonitorRule, ScanType, SourceType } from '@/types';

const fmt = (value: string | null, timeZone?: string) => value ? new Intl.DateTimeFormat(undefined, {
  year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  second: '2-digit', timeZone, timeZoneName: 'short',
}).format(new Date(value)) : '—';
const weekdayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const intervals = [15, 30, 60, 120, 360, 720, 1440] as const;
const timezones = ['Asia/Shanghai', 'Asia/Hong_Kong', 'Asia/Singapore', 'UTC', 'Europe/Berlin', 'America/New_York', 'America/Los_Angeles'];

function scheduleLabel(rule: MonitorRule) {
  if (rule.schedule_kind === 'CRON') return `Cron · ${rule.cron_expression} · ${rule.timezone}`;
  if (rule.schedule_kind === 'DAILY') return `Daily at ${rule.schedule_time.slice(0, 5)} · ${rule.timezone}`;
  if (rule.schedule_kind === 'WEEKLY') return `${rule.schedule_weekdays.map(day => weekdayNames[day]).join(', ')} at ${rule.schedule_time.slice(0, 5)} · ${rule.timezone}`;
  return `${rule.interval_minutes < 60 ? `Every ${rule.interval_minutes} minutes` : `Every ${rule.interval_minutes / 60} hours`} · ${rule.timezone}`;
}

export const Monitoring: React.FC<{ embedded?: boolean }> = ({ embedded = false }) => {
  const qc = useQueryClient();
  const [editing, setEditing] = useState<MonitorRule | null>(null);
  const { data: rules = [], isLoading, error } = useQuery({
    queryKey: ['monitor-rules'], queryFn: monitorRulesApi.list,
    refetchInterval: 5_000, refetchIntervalInBackground: false,
    refetchOnWindowFocus: true, staleTime: 0,
  });
  const scheduledRules = rules.filter(rule => rule.profile === null);
  const refresh = () => qc.invalidateQueries({ queryKey: ['monitor-rules'] });
  const updateRule = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<MonitorRule> }) => monitorRulesApi.update(id, data),
    onSuccess: () => { refresh(); setEditing(null); },
  });
  const deleteRule = useMutation({ mutationFn: monitorRulesApi.delete, onSuccess: () => { refresh(); qc.invalidateQueries({ queryKey: ['monitoring-profiles'] }); } });
  const runNow = useMutation({ mutationFn: monitorRulesApi.runNow, onSuccess: () => { refresh(); qc.invalidateQueries({ queryKey: ['scans'] }); } });

  return <div className="space-y-5">
    {!embedded && <div><h1 className="text-3xl font-bold">Monitoring Plans</h1><p className="mt-1 text-sm text-muted-foreground">Manage all scheduled scans.</p></div>}
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div><h2 className="text-lg font-semibold">Scheduled Scans</h2><p className="text-sm text-muted-foreground">{scheduledRules.length} plans; new plans are enabled by default.</p></div>
      <Link to="/scans/new?mode=schedule" className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">New Scheduled Scan</Link>
    </div>
    {isLoading ? <div className="rounded-xl border p-8 text-center text-muted-foreground">Loading...</div>
      : error ? <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-5 text-destructive">Failed to load monitoring plans</div>
      : scheduledRules.length === 0 ? <div className="rounded-xl border border-dashed p-10 text-center"><p className="font-medium">No scheduled scans yet</p><p className="mt-2 text-sm text-muted-foreground">Create a scan and choose scheduled execution to add your first plan.</p></div>
      : <div className="overflow-x-auto rounded-xl border bg-card shadow-sm"><table className="w-full min-w-[1040px] text-sm">
        <thead className="bg-muted/60 text-left text-xs text-muted-foreground"><tr><th className="px-4 py-3">Plan Name</th><th className="px-4 py-3">Scan Target</th><th className="px-4 py-3">Schedule</th><th className="px-4 py-3">Next Run</th><th className="px-4 py-3">Latest Scan</th><th className="px-4 py-3">Enabled</th><th className="px-4 py-3 text-right">Actions</th></tr></thead>
        <tbody className="divide-y">{scheduledRules.map(rule => <tr key={rule.id} className="hover:bg-muted/30">
          <td className="px-4 py-4"><p className="font-medium">{rule.name}</p><p className="mt-1 text-xs uppercase text-muted-foreground">{rule.source} · {rule.scan_type}</p></td>
          <td className="max-w-xs px-4 py-4"><p className="truncate font-mono text-xs" title={rule.value}>{rule.value}</p></td><td className="px-4 py-4">{scheduleLabel(rule)}</td><td className="whitespace-nowrap px-4 py-4">{rule.enabled ? fmt(rule.next_run_at, rule.timezone) : '—'}</td>
          <td className="px-4 py-4">{rule.last_scan ? <Link className="text-primary hover:underline" to={`/scans/${rule.last_scan}`}>#{rule.last_scan}</Link> : 'Never run'}</td>
          <td className="px-4 py-4"><button type="button" role="switch" aria-checked={rule.enabled} disabled={rule.is_running || updateRule.isPending} onClick={() => updateRule.mutate({ id: rule.id, data: { enabled: !rule.enabled } })} className={`relative h-6 w-11 rounded-full transition-colors disabled:opacity-50 ${rule.enabled ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'}`}><span className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${rule.enabled ? 'translate-x-5' : 'translate-x-0'}`}/></button><p className="mt-1 text-[10px] text-muted-foreground">{rule.is_running ? 'Running' : rule.enabled ? 'Enabled' : 'Disabled'}</p></td>
          <td className="whitespace-nowrap px-4 py-4 text-right"><button disabled={rule.is_running} onClick={() => setEditing(rule)} className="mr-3 text-foreground hover:underline disabled:opacity-50">Edit</button><button disabled={rule.is_running || runNow.isPending} onClick={() => runNow.mutate(rule.id)} className="mr-3 text-primary hover:underline disabled:opacity-50">{rule.is_running ? 'Running' : 'Run Now'}</button><button disabled={rule.is_running || deleteRule.isPending} onClick={() => { if (window.confirm(`Delete monitoring plan "${rule.name}"? Historical scans will be kept.`)) deleteRule.mutate(rule.id); }} className="text-destructive hover:underline disabled:opacity-50">Delete</button></td>
        </tr>)}</tbody></table></div>}
    {editing && <EditPlanModal rule={editing} busy={updateRule.isPending} onClose={() => setEditing(null)} onSave={data => updateRule.mutate({ id: editing.id, data })}/>}
  </div>;
};

function EditPlanModal({ rule, busy, onClose, onSave }: { rule: MonitorRule; busy: boolean; onClose: () => void; onSave: (data: Partial<MonitorRule>) => void }) {
  const [form, setForm] = useState(rule);
  useEffect(() => setForm(rule), [rule]);
  const set = <K extends keyof MonitorRule>(key: K, value: MonitorRule[K]) => setForm(current => ({ ...current, [key]: value }));
  const availableTypes: ScanType[] = form.source === 'github' ? ['org_repos', 'search_repos', 'search_code', 'search_commits', 'search_issues', 'search_users'] : form.source === 'brave' ? ['search_repos'] : ['org_repos', 'search_repos'];
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}>
    <form className="max-h-[90vh] w-full max-w-2xl space-y-4 overflow-y-auto rounded-xl border bg-card p-6 shadow-xl" onSubmit={event => { event.preventDefault(); onSave({ name: form.name, value: form.value, source: form.source, scan_type: form.scan_type, schedule_kind: form.schedule_kind, interval_minutes: form.interval_minutes, schedule_time: form.schedule_time, schedule_weekdays: form.schedule_weekdays, cron_expression: form.cron_expression, timezone: form.timezone }); }}>
      <div className="flex items-start justify-between"><div><h2 className="text-xl font-semibold">Edit Monitoring Plan</h2><p className="text-sm text-muted-foreground">Changes apply to future runs only.</p></div><button type="button" onClick={onClose} className="rounded-md border px-3 py-1">Close</button></div>
      <div className="grid gap-4 sm:grid-cols-2"><label className="text-sm"><span className="mb-1 block font-medium">Plan Name</span><input required value={form.name} onChange={e => set('name', e.target.value)} className="w-full rounded-md border bg-background px-3 py-2"/></label><label className="text-sm"><span className="mb-1 block font-medium">Scan Target</span><input required value={form.value} onChange={e => set('value', e.target.value)} className="w-full rounded-md border bg-background px-3 py-2"/></label></div>
      <div className="grid gap-4 sm:grid-cols-2"><label className="text-sm"><span className="mb-1 block font-medium">Source</span><select value={form.source} onChange={e => { const source=e.target.value as SourceType; setForm(current => ({...current, source, scan_type: source === 'brave' ? 'search_repos' : 'org_repos'})); }} className="w-full rounded-md border bg-background px-3 py-2"><option value="github">GitHub</option><option value="gitlab">GitLab</option><option value="gitee">Gitee</option><option value="brave">Brave Search</option></select></label><label className="text-sm"><span className="mb-1 block font-medium">Scan Type</span><select value={form.scan_type} onChange={e => set('scan_type', e.target.value as ScanType)} className="w-full rounded-md border bg-background px-3 py-2">{availableTypes.map(type => <option key={type} value={type}>{type}</option>)}</select></label></div>
      <div className="grid gap-4 sm:grid-cols-2"><label className="text-sm"><span className="mb-1 block font-medium">Schedule Type</span><select value={form.schedule_kind} onChange={e => set('schedule_kind', e.target.value as MonitorRule['schedule_kind'])} className="w-full rounded-md border bg-background px-3 py-2"><option value="INTERVAL">Fixed Interval</option><option value="DAILY">Daily</option><option value="WEEKLY">Weekly</option><option value="CRON">Cron</option></select></label>{form.schedule_kind === 'INTERVAL' && <label className="text-sm"><span className="mb-1 block font-medium">Interval</span><select value={form.interval_minutes} onChange={e => set('interval_minutes', Number(e.target.value) as MonitorRule['interval_minutes'])} className="w-full rounded-md border bg-background px-3 py-2">{intervals.map(value => <option key={value} value={value}>{value < 60 ? `${value} minutes` : `${value / 60} hours`}</option>)}</select></label>}{['DAILY','WEEKLY'].includes(form.schedule_kind) && <label className="text-sm"><span className="mb-1 block font-medium">Run Time</span><input type="time" required value={form.schedule_time.slice(0,5)} onChange={e => set('schedule_time', e.target.value)} className="w-full rounded-md border bg-background px-3 py-2"/></label>}</div>
      <label className="block text-sm"><span className="mb-1 block font-medium">Time Zone</span><select value={form.timezone} onChange={e => set('timezone', e.target.value)} className="w-full rounded-md border bg-background px-3 py-2">{timezones.map(zone => <option key={zone} value={zone}>{zone}</option>)}</select><small className="text-muted-foreground">Run time and Cron expression are interpreted in this time zone.</small></label>
      {form.schedule_kind === 'WEEKLY' && <div className="flex flex-wrap gap-2">{weekdayNames.map((name, day) => <label key={name} className={`cursor-pointer rounded-md border px-3 py-2 text-sm ${form.schedule_weekdays.includes(day) ? 'border-primary bg-primary/10' : ''}`}><input type="checkbox" className="mr-2" checked={form.schedule_weekdays.includes(day)} onChange={() => set('schedule_weekdays', form.schedule_weekdays.includes(day) ? form.schedule_weekdays.filter(value => value !== day) : [...form.schedule_weekdays, day])}/>{name}</label>)}</div>}
      {form.schedule_kind === 'CRON' && <label className="text-sm"><span className="mb-1 block font-medium">Cron Expression</span><input required value={form.cron_expression} onChange={e => set('cron_expression', e.target.value)} className="w-full rounded-md border bg-background px-3 py-2 font-mono"/><small className="text-muted-foreground">Five fields: minute hour day month weekday</small></label>}
      <div className="flex justify-end gap-3 border-t pt-4"><button type="button" onClick={onClose} className="rounded-lg border px-4 py-2">Cancel</button><button disabled={busy} className="rounded-lg bg-primary px-5 py-2 text-primary-foreground disabled:opacity-50">{busy ? 'Saving...' : 'Save Changes'}</button></div>
    </form>
  </div>;
}
