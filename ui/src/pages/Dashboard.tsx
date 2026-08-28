import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/services/api';
import { LiveIndicator } from '@/components/LiveIndicator';
import { AlertTriangle, CheckCircle2, GitBranch, Github, GitFork, Gitlab, Mountain, Search, ShieldCheck } from 'lucide-react';

const healthStyle: Record<string, string> = {
  HEALTHY: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  WARNING: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
  CRITICAL: 'bg-red-500/10 text-red-600 dark:text-red-400',
  UNKNOWN: 'bg-slate-500/10 text-slate-600 dark:text-slate-400',
};
const severityStyle: Record<string, string> = {
  CRITICAL: 'border-red-500/30 bg-red-500/5 text-red-600 dark:text-red-400',
  HIGH: 'border-orange-500/30 bg-orange-500/5 text-orange-600 dark:text-orange-400',
  MEDIUM: 'border-amber-500/30 bg-amber-500/5 text-amber-600 dark:text-amber-400',
  LOW: 'border-blue-500/30 bg-blue-500/5 text-blue-600 dark:text-blue-400',
  INFO: 'border-slate-500/30 bg-slate-500/5 text-slate-600 dark:text-slate-400',
};
const statusDot: Record<string, string> = { SUCCESS:'bg-emerald-500', DEGRADED:'bg-amber-500', FAILED:'bg-red-500', RUNNING:'bg-blue-500', QUEUED:'bg-slate-400' };
const sources = [
  { key:'github', label:'GitHub', icon:Github, color:'text-violet-600 dark:text-violet-400' },
  { key:'gitlab', label:'GitLab', icon:Gitlab, color:'text-orange-600 dark:text-orange-400' },
  { key:'gitee', label:'Gitee', icon:GitFork, color:'text-red-600 dark:text-red-400' },
  { key:'bitbucket', label:'Bitbucket', icon:GitBranch, color:'text-blue-600 dark:text-blue-400' },
  { key:'codeberg', label:'Codeberg', icon:Mountain, color:'text-teal-600 dark:text-teal-400' },
  { key:'brave', label:'Brave', icon:Search, color:'text-orange-500 dark:text-orange-300' },
];

export const Dashboard: React.FC = () => {
  const { data, isLoading, error } = useQuery({ queryKey:['dashboard'], queryFn:dashboardApi.get, refetchInterval:5_000, refetchIntervalInBackground:false, refetchOnWindowFocus:true, staleTime:0 });
  if (isLoading) return <div className="animate-pulse space-y-4"><div className="h-10 w-52 rounded bg-muted"/><div className="h-28 rounded-xl bg-muted"/><div className="h-64 rounded-xl bg-muted"/></div>;
  if (error || !data) return <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-destructive">Failed to load dashboard</div>;
  const maxTrend = Math.max(1, ...data.scan_trend.map(item => item.count));
  const totalFindings = Object.values(data.severity_counts).reduce((sum, count) => sum + count, 0);

  return <div className="space-y-5">
    <header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-medium text-primary">Security overview</p><div className="mt-1 flex items-center gap-3"><h1 className="text-3xl font-bold">Dashboard</h1><LiveIndicator /></div><p className="mt-1 text-sm text-muted-foreground">持续代码与敏感信息泄漏监控概览</p></div><div className="flex gap-2"><Link to="/scans?tab=monitors" className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-muted">Monitoring Plans</Link><Link to="/scans/new" className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">New Scan</Link></div></header>

    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <div className="rounded-xl border bg-card p-4 shadow-sm"><div className="flex items-center justify-between"><p className="text-xs text-muted-foreground">Overall Health</p>{data.overall_health === 'HEALTHY' ? <ShieldCheck className="h-5 w-5 text-emerald-500"/> : <AlertTriangle className="h-5 w-5 text-amber-500"/>}</div><div className="mt-2 flex items-center justify-between"><span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${healthStyle[data.overall_health]}`}>{data.overall_health}</span><span className="text-xs text-muted-foreground">{data.source_health.length} sources</span></div></div>
      <Metric label="New Findings" value={data.new_findings} hint="NEW + REOPENED" accent="text-red-600 dark:text-red-400" />
      <Metric label="All Findings" value={totalFindings} hint="Current lifecycle" />
      <Metric label="Resolved" value={data.resolved_findings} hint="Remediated findings" accent="text-emerald-600 dark:text-emerald-400" />
    </section>

    <section><div className="mb-2 flex items-center justify-between"><div><h2 className="text-base font-semibold">Risk distribution</h2><p className="text-xs text-muted-foreground">按 Finding 风险等级统计</p></div><Link to="/findings" className="text-sm font-medium text-primary">View findings →</Link></div><div className="grid grid-cols-2 gap-2 md:grid-cols-5">{(['CRITICAL','HIGH','MEDIUM','LOW','INFO'] as const).map(level => <div key={level} className={`flex items-center justify-between rounded-lg border px-3 py-2 ${severityStyle[level]}`}><p className="text-[11px] font-semibold tracking-wide">{level}</p><p className="text-xl font-bold">{data.severity_counts[level]}</p></div>)}</div></section>

    <div className="grid gap-4 xl:grid-cols-3">
      <section className="rounded-xl border bg-card p-4 shadow-sm xl:col-span-2"><div className="mb-3 flex items-center justify-between"><div><h2 className="text-base font-semibold">Scan Trend</h2><p className="text-xs text-muted-foreground">最近 14 天扫描次数</p></div><Link to="/scans?tab=history" className="text-sm text-primary">Task history →</Link></div><div className="flex h-40 items-end gap-1.5 border-b border-l px-2 pt-7">{data.scan_trend.map((item, index) => <div key={item.date} className="group relative flex h-full min-w-0 flex-1 items-end"><div className="relative w-full rounded-t bg-sky-500 transition-colors hover:bg-sky-400 dark:bg-sky-400 dark:hover:bg-sky-300" style={{height:`${item.count === 0 ? 2 : Math.max(10, item.count / maxTrend * 100)}%`}}><span className="absolute -top-5 left-1/2 -translate-x-1/2 text-[10px] font-semibold text-foreground">{item.count}</span><div className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-7 hidden -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-900 px-2 py-1 text-xs text-white shadow-lg group-hover:block">{item.date} · {item.count} scans</div></div>{(index % 2 === 0 || index === data.scan_trend.length - 1) && <span className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[9px] text-muted-foreground">{item.date.slice(5)}</span>}</div>)}</div><div className="h-5"/></section>

      <section className="rounded-xl border bg-card p-4 shadow-sm"><div className="mb-3 flex items-center justify-between"><h2 className="text-base font-semibold">Source Health</h2><Link to="/source-health" className="text-sm text-primary">View all</Link></div><div className="grid grid-cols-3 gap-2">{sources.map(source => { const item=data.source_health.find(health=>health.source===source.key); const healthy=item?.status==='HEALTHY'; const Icon=source.icon; return <div key={source.key} title={`${source.label}: ${item?.status || 'UNKNOWN'} · Results ${item?.result_count ?? 0} · New ${item?.new_findings ?? 0}`} className="relative flex flex-col items-center rounded-lg border p-3 text-center hover:bg-muted/50"><Icon className={`h-7 w-7 ${healthy ? source.color : 'text-slate-300 dark:text-slate-600'}`}/><p className={`mt-1 text-[11px] font-medium ${healthy ? '' : 'text-muted-foreground'}`}>{source.label}</p><span className={`absolute right-2 top-2 h-2 w-2 rounded-full ${healthy ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'}`}/></div>; })}</div><div className="mt-3 flex items-center justify-between text-[10px] text-muted-foreground"><span className="flex items-center gap-1"><CheckCircle2 className="h-3 w-3 text-emerald-500"/>彩色：健康</span><span>灰色：异常或未配置</span></div></section>
    </div>

    <div className="grid gap-4 lg:grid-cols-2">
      <section className="rounded-xl border bg-card shadow-sm"><div className="flex items-center justify-between border-b px-4 py-3"><h2 className="font-semibold">Recent Scans</h2><Link to="/scans?tab=history" className="text-sm text-primary">View all</Link></div>{data.recent_scans.length === 0 ? <Empty text="No scans yet"/> : <div className="divide-y">{data.recent_scans.map(scan => <Link key={scan.id} to={`/scans/${scan.id}`} className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-muted/60"><div className="min-w-0"><p className="truncate text-sm font-medium">{scan.value}</p><p className="mt-0.5 text-xs text-muted-foreground">{scan.source} · {scan.trigger_type} · {new Date(scan.created_at).toLocaleString()}</p></div><span className="flex shrink-0 items-center gap-2 text-xs"><i className={`h-2 w-2 rounded-full ${statusDot[scan.execution_status] || 'bg-slate-400'}`}/>{scan.execution_status}</span></Link>)}</div>}</section>
      <section className="rounded-xl border bg-card shadow-sm"><div className="flex items-center justify-between border-b p-5"><h2 className="font-semibold">Recent Findings</h2><Link to="/findings" className="text-sm text-primary">View all</Link></div>{data.recent_findings.length === 0 ? <Empty text="No findings yet"/> : <div className="divide-y">{data.recent_findings.map(finding => <div key={finding.id} className="flex items-center justify-between gap-4 p-4"><div className="min-w-0"><p className="truncate text-sm font-medium">{finding.type}</p><p className="mt-1 truncate text-xs text-muted-foreground">{finding.repository} · {finding.lifecycle_status}</p></div><span className={`shrink-0 rounded-full border px-2 py-1 text-xs font-semibold ${severityStyle[finding.severity]}`}>{finding.severity}</span></div>)}</div>}</section>
    </div>
  </div>;
};

const Metric = ({label,value,hint,accent=''}:{label:string;value:number;hint:string;accent?:string}) => <div className="rounded-xl border bg-card p-4 shadow-sm"><p className="text-xs text-muted-foreground">{label}</p><div className="mt-1 flex items-end justify-between"><p className={`text-2xl font-bold ${accent}`}>{value}</p><p className="text-[10px] text-muted-foreground">{hint}</p></div></div>;
const Empty = ({text}:{text:string}) => <p className="p-8 text-center text-sm text-muted-foreground">{text}</p>;
