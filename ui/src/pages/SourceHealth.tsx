import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { sourceHealthApi } from '@/services/api';

export const SourceHealth: React.FC = () => {
  const { data=[], isLoading } = useQuery({queryKey:['source-health'],queryFn:sourceHealthApi.list});
  return <div className="space-y-6"><h1 className="text-3xl font-bold">Source Health</h1>{isLoading?<p>Loading...</p>:<div className="grid md:grid-cols-2 gap-4">{data.map(item=><div key={item.id} className="border rounded-lg bg-card p-5"><div className="flex justify-between"><strong className="capitalize">{item.source}</strong><span>{item.status}</span></div><div className="mt-4 text-sm space-y-2"><p>Last success: {item.last_success_at?new Date(item.last_success_at).toLocaleString():'—'}</p><p>Results: {item.result_count}</p><p>New findings: {item.new_findings}</p><p>Rate limit: {item.rate_limit_remaining??'—'}</p>{item.error_message&&<p className="text-destructive">{item.error_message}</p>}</div></div>)}</div>}</div>;
};
