import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { monitoringProfilesApi } from '@/services/api';
import type { MonitorRule } from '@/types';

const split = (value: string) => value.split(',').map(item => item.trim()).filter(Boolean);

export const MonitoringProfiles: React.FC = () => {
  const qc = useQueryClient();
  const { data = [] } = useQuery({ queryKey: ['monitoring-profiles'], queryFn: monitoringProfilesApi.list });
  const [form, setForm] = useState({ name: '', company: '', domains: '', github: '', gitlab: '', keywords: '', interval: 60 as MonitorRule['interval_minutes'] });
  const create = useMutation({ mutationFn: monitoringProfilesApi.create, onSuccess: () => { qc.invalidateQueries({ queryKey: ['monitoring-profiles'] }); qc.invalidateQueries({ queryKey: ['monitor-rules'] }); setForm({ ...form, name: '', company: '', domains: '', github: '', gitlab: '', keywords: '' }); } });
  const remove = useMutation({ mutationFn: monitoringProfilesApi.delete, onSuccess: () => { qc.invalidateQueries({ queryKey: ['monitoring-profiles'] }); qc.invalidateQueries({ queryKey: ['monitor-rules'] }); } });
  return <div className="space-y-6"><h1 className="text-3xl font-bold">Monitoring Profiles</h1>
    <form className="grid md:grid-cols-2 gap-3 border rounded-lg p-4 bg-card" onSubmit={event => { event.preventDefault(); create.mutate({ name: form.name, enabled: true, company_name: form.company, domains: split(form.domains), email_domains: [], brands: [], product_names: [], internal_projects: [], internal_domains: [], github_orgs: split(form.github), gitlab_groups: split(form.gitlab), custom_keywords: split(form.keywords), interval_minutes: form.interval }); }}>
      <input required className="border rounded px-3 py-2" placeholder="Profile name" value={form.name} onChange={e => setForm({...form, name:e.target.value})}/>
      <input className="border rounded px-3 py-2" placeholder="Company name" value={form.company} onChange={e => setForm({...form, company:e.target.value})}/>
      <input className="border rounded px-3 py-2" placeholder="Domains (comma separated)" value={form.domains} onChange={e => setForm({...form, domains:e.target.value})}/>
      <input className="border rounded px-3 py-2" placeholder="GitHub Orgs" value={form.github} onChange={e => setForm({...form, github:e.target.value})}/>
      <input className="border rounded px-3 py-2" placeholder="GitLab Groups" value={form.gitlab} onChange={e => setForm({...form, gitlab:e.target.value})}/>
      <input className="border rounded px-3 py-2" placeholder="Custom keywords" value={form.keywords} onChange={e => setForm({...form, keywords:e.target.value})}/>
      <select value={form.interval} onChange={e => setForm({...form,interval:Number(e.target.value) as MonitorRule['interval_minutes']})}>{[15,30,60,120,360,720,1440].map(value=><option key={value} value={value}>{value} min</option>)}</select>
      <button className="bg-primary text-primary-foreground rounded">Create Profile</button>
    </form>
    <div className="border rounded-lg divide-y bg-card">{data.map(profile=><div key={profile.id} className="p-4 flex justify-between"><div><strong>{profile.name}</strong><p className="text-sm text-muted-foreground">{profile.company_name || '—'} · {profile.generated_rule_count} generated rules</p></div><button className="text-destructive" onClick={()=>remove.mutate(profile.id)}>Delete</button></div>)}</div>
  </div>;
};
