import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/services/api';

const healthStyle: Record<string, string> = { HEALTHY:'text-green-600', WARNING:'text-orange-600', CRITICAL:'text-red-600', UNKNOWN:'text-gray-600' };

export const Dashboard: React.FC = () => {
  const { data, isLoading, error } = useQuery({ queryKey:['dashboard'], queryFn:dashboardApi.get });
  if (isLoading) return <p>Loading...</p>;
  if (error || !data) return <p className="text-destructive">Failed to load dashboard</p>;
  const maxTrend = Math.max(1, ...data.scan_trend.map(item => item.count));
  return <div className="space-y-8">
    <div className="flex justify-between"><h1 className="text-3xl font-bold">Dashboard</h1><Link to="/scans/new" className="px-4 py-2 bg-primary text-primary-foreground rounded-lg">New Scan</Link></div>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Metric label="Overall Health" value={data.overall_health} className={healthStyle[data.overall_health]} />
      <Metric label="New Findings" value={data.new_findings} /><Metric label="Resolved" value={data.resolved_findings} /><Metric label="Sources" value={data.source_health.length} />
    </div>
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">{(['CRITICAL','HIGH','MEDIUM','LOW','INFO'] as const).map(level=><Metric key={level} label={level} value={data.severity_counts[level]} />)}</div>
    <section><div className="flex justify-between mb-3"><h2 className="text-xl font-semibold">Source Health</h2><Link to="/source-health" className="text-primary">View all</Link></div><div className="grid md:grid-cols-3 gap-4">{data.source_health.map(item=><div key={item.id} className="p-4 border rounded-lg bg-card"><div className="flex justify-between"><strong className="capitalize">{item.source}</strong><span className={healthStyle[item.status]}>{item.status}</span></div><p className="text-sm mt-3">Results: {item.result_count} · New: {item.new_findings}</p><p className="text-xs text-muted-foreground">Rate limit: {item.rate_limit_remaining ?? '—'}</p></div>)}</div></section>
    <section><h2 className="text-xl font-semibold mb-3">Scan Trend</h2><div className="h-36 flex items-end gap-2 border rounded-lg bg-card p-4">{data.scan_trend.map(item=><div key={item.date} className="flex-1 min-w-3 bg-primary rounded-t" title={`${item.date}: ${item.count}`} style={{height:`${Math.max(5,item.count/maxTrend*100)}%`}} />)}</div></section>
    <section><h2 className="text-xl font-semibold mb-3">Recent Scans</h2><div className="border rounded-lg divide-y bg-card">{data.recent_scans.map(scan=><Link key={scan.id} to={`/scans/${scan.id}`} className="flex justify-between p-4 hover:bg-muted"><span>{scan.source} · {scan.value}</span><span>{scan.execution_status}</span></Link>)}</div></section>
    <section><h2 className="text-xl font-semibold mb-3">Recent Findings</h2><div className="border rounded-lg divide-y bg-card">{data.recent_findings.map(finding=><div key={finding.id} className="flex justify-between p-4"><span>{finding.type} · {finding.repository}</span><span>{finding.severity}</span></div>)}</div></section>
  </div>;
};

const Metric = ({label,value,className=''}:{label:string;value:string|number;className?:string}) => <div className="p-5 border rounded-lg bg-card"><p className="text-sm text-muted-foreground">{label}</p><p className={`text-2xl font-bold mt-2 ${className}`}>{value}</p></div>;
