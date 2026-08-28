import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { sourceHealthApi } from '@/services/api';

export const SourceHealth: React.FC = () => {
  const { data = [], isLoading } = useQuery({ queryKey: ['source-health'], queryFn: sourceHealthApi.list, refetchInterval: 5_000 });
  return <div className="space-y-6">
    <p className="text-sm text-muted-foreground">Integration connectivity and the latest scan health are shown separately from Finding severity.</p>
    {isLoading ? <p>Loading...</p> : <div className="grid gap-4 md:grid-cols-2">{data.map(item => {
      const connected = item.integration_status === 'connected';
      return <div key={item.id} className="rounded-lg border bg-card p-5">
        <div className="flex items-start justify-between"><div><strong className="capitalize">{item.source}</strong><p className="mt-1 text-xs text-muted-foreground">Integration: <span className={connected ? 'text-emerald-600' : 'text-amber-600'}>{item.integration_status}</span></p></div><span className={`rounded-full px-2 py-1 text-xs ${item.status === 'HEALTHY' ? 'bg-emerald-500/10 text-emerald-600' : 'bg-amber-500/10 text-amber-600'}`}>{item.status}</span></div>
        <div className="mt-4 space-y-2 text-sm"><p>Last checked: {item.last_checked_at ? new Date(item.last_checked_at).toLocaleString() : '—'}</p><p>Last success: {item.last_success_at ? new Date(item.last_success_at).toLocaleString() : '—'}</p><p>Results: {item.result_count}</p><p>New findings: {item.new_findings}</p><p>Rate limit: {item.rate_limit_remaining ?? '—'}</p>{item.error_message && <p className="text-destructive">{item.error_message}</p>}</div>
      </div>;
    })}</div>}
  </div>;
};
