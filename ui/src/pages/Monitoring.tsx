import React, { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { monitorRulesApi, monitoringProfilesApi } from '@/services/api';
import type { MonitorRule, ScanType, SourceType } from '@/types';

const intervals = [15, 30, 60, 120, 360, 720, 1440] as const;
const split = (value: string) => value.split(',').map(item => item.trim()).filter(Boolean);
const fmt = (value: string | null) => value ? new Date(value).toLocaleString() : '—';

export const Monitoring: React.FC = () => {
  const qc = useQueryClient();
  const { data: profiles = [] } = useQuery({ queryKey: ['monitoring-profiles'], queryFn: monitoringProfilesApi.list });
  const { data: rules = [] } = useQuery({ queryKey: ['monitor-rules'], queryFn: monitorRulesApi.list, refetchInterval: 30_000 });
  const [advanced, setAdvanced] = useState(false);
  const [profile, setProfile] = useState({ name: '', company: '', domains: '', emails: '', brands: '', products: '', projects: '', internalDomains: '', github: '', gitlab: '', keywords: '', interval: 60 as MonitorRule['interval_minutes'] });
  const [rule, setRule] = useState({ name: '', value: '', source: 'github' as SourceType, scan_type: 'search_repos' as ScanType, interval_minutes: 60 as MonitorRule['interval_minutes'] });
  const refresh = () => { qc.invalidateQueries({ queryKey: ['monitoring-profiles'] }); qc.invalidateQueries({ queryKey: ['monitor-rules'] }); };
  const createProfile = useMutation({ mutationFn: monitoringProfilesApi.create, onSuccess: () => { refresh(); setProfile({ ...profile, name: '', company: '', domains: '', emails: '', brands: '', products: '', projects: '', internalDomains: '', github: '', gitlab: '', keywords: '' }); } });
  const deleteProfile = useMutation({ mutationFn: monitoringProfilesApi.delete, onSuccess: refresh });
  const createRule = useMutation({ mutationFn: monitorRulesApi.create, onSuccess: () => { refresh(); setRule({ ...rule, name: '', value: '' }); } });
  const deleteRule = useMutation({ mutationFn: monitorRulesApi.delete, onSuccess: refresh });
  const rulesByProfile = useMemo(() => new Map(profiles.map(item => [item.id, rules.filter(ruleItem => ruleItem.profile === item.id)])), [profiles, rules]);

  return <div className="space-y-6">
    <div><h1 className="text-3xl font-bold">Monitoring</h1><p className="mt-1 text-sm text-muted-foreground">用一个监控配置维护资产与关键词，系统会自动生成定时扫描规则。</p></div>
    <section className="rounded-xl border bg-card p-5 shadow-sm">
      <div className="mb-4"><h2 className="text-lg font-semibold">新建监控配置</h2><p className="text-sm text-muted-foreground">逗号分隔多个值；保存后会立即进入第一次调度。</p></div>
      <form className="grid gap-3 md:grid-cols-2" onSubmit={event => { event.preventDefault(); createProfile.mutate({ name: profile.name, enabled: true, company_name: profile.company, domains: split(profile.domains), email_domains: split(profile.emails), brands: split(profile.brands), product_names: split(profile.products), internal_projects: split(profile.projects), internal_domains: split(profile.internalDomains), github_orgs: split(profile.github), gitlab_groups: split(profile.gitlab), custom_keywords: split(profile.keywords), interval_minutes: profile.interval }); }}>
        <input required className="rounded-md border bg-background px-3 py-2" placeholder="配置名称 *" value={profile.name} onChange={e => setProfile({...profile,name:e.target.value})}/><input className="rounded-md border bg-background px-3 py-2" placeholder="公司名称" value={profile.company} onChange={e => setProfile({...profile,company:e.target.value})}/>
        {[['domains','域名'],['emails','邮箱域名'],['brands','品牌'],['products','产品名'],['projects','内部项目名'],['internalDomains','内部域名'],['github','GitHub Orgs'],['gitlab','GitLab Groups'],['keywords','自定义关键词']].map(([key,label]) => <input key={key} className="rounded-md border bg-background px-3 py-2" placeholder={`${label}（逗号分隔）`} value={profile[key as keyof typeof profile] as string} onChange={e => setProfile({...profile,[key]:e.target.value})}/>)}
        <select className="rounded-md border bg-background px-3 py-2" value={profile.interval} onChange={e => setProfile({...profile,interval:Number(e.target.value) as MonitorRule['interval_minutes']})}>{intervals.map(value => <option key={value} value={value}>{value < 60 ? `${value} 分钟` : `${value / 60} 小时`}</option>)}</select>
        <button disabled={createProfile.isPending} className="rounded-md bg-primary px-4 py-2 font-medium text-primary-foreground disabled:opacity-50">{createProfile.isPending ? '创建中…' : '创建并启用监控'}</button>
      </form>
    </section>
    <section className="space-y-3"><div className="flex items-center justify-between"><h2 className="text-lg font-semibold">已启用的监控</h2><span className="text-sm text-muted-foreground">{profiles.length} 个配置 · {rules.length} 条规则</span></div>
      {profiles.length === 0 && <div className="rounded-xl border border-dashed p-8 text-center text-muted-foreground">尚无监控配置</div>}
      {profiles.map(item => { const children = rulesByProfile.get(item.id) || []; return <div key={item.id} className="rounded-xl border bg-card p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><div className="flex items-center gap-2"><h3 className="font-semibold">{item.name}</h3><span className={`rounded-full px-2 py-0.5 text-xs ${item.enabled?'bg-green-500/10 text-green-700':'bg-slate-500/10 text-slate-600'}`}>{item.enabled?'已启用':'已停用'}</span></div><p className="mt-1 text-sm text-muted-foreground">{item.company_name || '未设置公司名'} · {item.interval_minutes} 分钟一次 · {children.length} 条自动规则</p></div><button className="text-sm text-destructive" onClick={() => deleteProfile.mutate(item.id)}>删除</button></div>
        <div className="mt-4 overflow-x-auto"><table className="w-full text-sm"><thead className="text-left text-muted-foreground"><tr><th className="pb-2">监控目标</th><th className="pb-2">数据源</th><th className="pb-2">下次执行</th><th className="pb-2">最近 Scan</th><th className="pb-2">状态</th></tr></thead><tbody>{children.map(child => <tr key={child.id} className="border-t"><td className="py-2 pr-3">{child.value}</td><td>{child.source}</td><td>{fmt(child.next_run_at)}</td><td>{child.last_scan ? `#${child.last_scan}` : '尚未生成'}</td><td><span className="rounded-full bg-blue-500/10 px-2 py-1 text-xs text-blue-700">{child.is_running?'执行中':child.enabled?'等待调度':'已停用'}</span></td></tr>)}</tbody></table></div></div>; })}
    </section>
    <section className="rounded-xl border bg-card"><button className="flex w-full items-center justify-between p-5 text-left" onClick={() => setAdvanced(!advanced)}><span><strong>高级：手动规则</strong><span className="ml-2 text-sm font-normal text-muted-foreground">仅用于无法由监控配置表达的特殊目标</span></span><span>{advanced?'−':'+'}</span></button>{advanced && <div className="border-t p-5"><form className="grid gap-3 md:grid-cols-5" onSubmit={e => { e.preventDefault(); createRule.mutate({...rule,enabled:true}); }}><input required className="rounded-md border px-3 py-2" placeholder="规则名称" value={rule.name} onChange={e=>setRule({...rule,name:e.target.value})}/><input required className="rounded-md border px-3 py-2" placeholder="目标或查询" value={rule.value} onChange={e=>setRule({...rule,value:e.target.value})}/><select value={rule.source} onChange={e=>{const source=e.target.value as SourceType;setRule({...rule,source,scan_type:source==='brave'?'search_repos':'org_repos'});}}><option value="github">GitHub</option><option value="gitlab">GitLab</option><option value="gitee">Gitee</option><option value="brave">Brave</option></select><select value={rule.interval_minutes} onChange={e=>setRule({...rule,interval_minutes:Number(e.target.value) as MonitorRule['interval_minutes']})}>{intervals.map(v=><option key={v} value={v}>{v} min</option>)}</select><button className="rounded-md bg-secondary px-3 py-2">添加规则</button></form><div className="mt-4 divide-y">{rules.filter(item=>!item.auto_generated).map(item=><div key={item.id} className="flex justify-between py-3 text-sm"><span>{item.name} · {item.source} · {item.value} · 下次 {fmt(item.next_run_at)}</span><button className="text-destructive" onClick={()=>deleteRule.mutate(item.id)}>删除</button></div>)}</div></div>}</section>
  </div>;
};
