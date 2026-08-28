import React from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { monitorRulesApi } from '@/services/api';
import type { MonitorRule } from '@/types';

const fmt = (value: string | null) => value ? new Date(value).toLocaleString() : '—';
const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

function scheduleLabel(rule: MonitorRule) {
  if (rule.schedule_kind === 'CRON') return `Cron · ${rule.cron_expression}`;
  if (rule.schedule_kind === 'DAILY') return `每天 ${rule.schedule_time.slice(0, 5)}`;
  if (rule.schedule_kind === 'WEEKLY') {
    return `${rule.schedule_weekdays.map(day => weekdays[day]).join('、')} ${rule.schedule_time.slice(0, 5)}`;
  }
  return rule.interval_minutes < 60
    ? `每 ${rule.interval_minutes} 分钟`
    : `每 ${rule.interval_minutes / 60} 小时`;
}

export const Monitoring: React.FC<{ embedded?: boolean }> = ({ embedded = false }) => {
  const qc = useQueryClient();
  const { data: rules = [], isLoading, error } = useQuery({
    queryKey: ['monitor-rules'],
    queryFn: monitorRulesApi.list,
    refetchInterval: 30_000,
  });
  const scheduledRules = rules.filter(rule => rule.profile === null);
  const refresh = () => qc.invalidateQueries({ queryKey: ['monitor-rules'] });
  const updateRule = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) => monitorRulesApi.update(id, { enabled }),
    onSuccess: refresh,
  });
  const deleteRule = useMutation({
    mutationFn: monitorRulesApi.delete,
    onSuccess: () => { refresh(); qc.invalidateQueries({ queryKey: ['monitoring-profiles'] }); },
  });
  const runNow = useMutation({
    mutationFn: monitorRulesApi.runNow,
    onSuccess: () => { refresh(); qc.invalidateQueries({ queryKey: ['scans'] }); },
  });

  return <div className="space-y-5">
    {!embedded && <div><h1 className="text-3xl font-bold">监控计划</h1><p className="mt-1 text-sm text-muted-foreground">管理所有定时扫描任务。</p></div>}
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div><h2 className="text-lg font-semibold">定时扫描任务</h2><p className="text-sm text-muted-foreground">共 {scheduledRules.length} 条；新任务默认启用。</p></div>
      <Link to="/scans/new?mode=schedule" className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">新建定时扫描</Link>
    </div>

    {isLoading ? <div className="rounded-xl border p-8 text-center text-muted-foreground">加载中…</div>
      : error ? <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-5 text-destructive">监控计划加载失败</div>
      : scheduledRules.length === 0 ? <div className="rounded-xl border border-dashed p-10 text-center"><p className="font-medium">暂无定时扫描任务</p><p className="mt-2 text-sm text-muted-foreground">通过“新建扫描”选择“定时执行”创建第一条计划。</p></div>
      : <div className="overflow-x-auto rounded-xl border bg-card shadow-sm"><table className="w-full min-w-[980px] text-sm">
        <thead className="bg-muted/60 text-left text-xs text-muted-foreground"><tr><th className="px-4 py-3">计划名称</th><th className="px-4 py-3">扫描目标</th><th className="px-4 py-3">执行计划</th><th className="px-4 py-3">下次执行</th><th className="px-4 py-3">最近 Scan</th><th className="px-4 py-3">启用</th><th className="px-4 py-3 text-right">操作</th></tr></thead>
        <tbody className="divide-y">{scheduledRules.map(rule => <tr key={rule.id} className="hover:bg-muted/30">
          <td className="px-4 py-4"><p className="font-medium">{rule.name}</p><p className="mt-1 text-xs uppercase text-muted-foreground">{rule.source} · {rule.scan_type}</p></td>
          <td className="max-w-xs px-4 py-4"><p className="truncate font-mono text-xs" title={rule.value}>{rule.value}</p></td>
          <td className="px-4 py-4">{scheduleLabel(rule)}</td>
          <td className="whitespace-nowrap px-4 py-4">{rule.enabled ? fmt(rule.next_run_at) : '—'}</td>
          <td className="px-4 py-4">{rule.last_scan ? <Link className="text-primary hover:underline" to={`/scans/${rule.last_scan}`}>#{rule.last_scan}</Link> : '尚未执行'}</td>
          <td className="px-4 py-4"><button type="button" role="switch" aria-checked={rule.enabled} disabled={rule.is_running || updateRule.isPending} onClick={() => updateRule.mutate({ id: rule.id, enabled: !rule.enabled })} className={`relative h-6 w-11 rounded-full transition-colors disabled:opacity-50 ${rule.enabled ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'}`}><span className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${rule.enabled ? 'translate-x-5' : 'translate-x-0'}`}/></button><p className="mt-1 text-[10px] text-muted-foreground">{rule.is_running ? '执行中' : rule.enabled ? '已启用' : '已停用'}</p></td>
          <td className="whitespace-nowrap px-4 py-4 text-right"><button disabled={rule.is_running || runNow.isPending} onClick={() => runNow.mutate(rule.id)} className="mr-3 text-primary hover:underline disabled:opacity-50">{rule.is_running ? '执行中' : '立即执行'}</button><button disabled={rule.is_running || deleteRule.isPending} onClick={() => { if (window.confirm(`确定删除监控计划“${rule.name}”吗？历史 Scan 不会删除。`)) deleteRule.mutate(rule.id); }} className="text-destructive hover:underline disabled:opacity-50">删除</button></td>
        </tr>)}</tbody>
      </table></div>}
  </div>;
};
