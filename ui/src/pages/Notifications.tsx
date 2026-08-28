import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Bell, Mail, Plus, Trash2, Webhook } from 'lucide-react';
import { notificationChannelsApi } from '@/services/api';
import type { NotificationChannel } from '@/types';

export const Notifications: React.FC = () => {
  const qc = useQueryClient();
  const { data = [], isLoading } = useQuery({
    queryKey: ['notification-channels'],
    queryFn: notificationChannelsApi.list,
    refetchInterval: 5_000,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
    staleTime: 0,
  });
  const [showForm, setShowForm] = useState(data.length === 0);
  const [form, setForm] = useState({ name:'', channel_type:'email' as 'email'|'webhook', target:'', enabled:true });
  const refresh = () => qc.invalidateQueries({ queryKey:['notification-channels'] });
  const add = useMutation({ mutationFn:notificationChannelsApi.create, onSuccess:() => { refresh(); setForm({...form,name:'',target:''}); setShowForm(false); } });
  const update = useMutation({ mutationFn:({channel,enabled}:{channel:NotificationChannel;enabled:boolean}) => notificationChannelsApi.update(channel.id,{enabled}), onSuccess:refresh });
  const remove = useMutation({ mutationFn:notificationChannelsApi.delete, onSuccess:refresh });

  return <div className="space-y-5">
    <div className="flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-2 text-sm text-muted-foreground"><Bell className="h-4 w-4"/><span>CRITICAL/HIGH 立即通知；默认仅发送 NEW 和 REOPENED Finding。</span></div><button onClick={() => setShowForm(!showForm)} className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"><Plus className="h-4 w-4"/>{showForm ? '收起' : '新增通知渠道'}</button></div>

    {showForm && <form className="rounded-xl border bg-card p-5 shadow-sm" onSubmit={event => {event.preventDefault();add.mutate(form);}}>
      <div className="mb-4 grid gap-3 sm:grid-cols-2">
        {(['email','webhook'] as const).map(type => { const Icon=type==='email'?Mail:Webhook; return <button type="button" key={type} onClick={() => setForm({...form,channel_type:type,target:''})} className={`flex items-center gap-3 rounded-lg border p-3 text-left ${form.channel_type===type?'border-primary bg-primary/5':''}`}><span className={`rounded-lg p-2 ${form.channel_type===type?'bg-primary/10 text-primary':'bg-muted text-muted-foreground'}`}><Icon className="h-5 w-5"/></span><span><strong className="block text-sm">{type==='email'?'Email':'Webhook'}</strong><small className="text-muted-foreground">{type==='email'?'发送到安全团队邮箱':'推送到 HTTPS 接收端点'}</small></span></button>;})}
      </div>
      <div className="grid gap-4 md:grid-cols-2"><label className="text-sm"><span className="mb-1.5 block font-medium">渠道名称</span><input required className="w-full rounded-md border bg-background px-3 py-2" placeholder={form.channel_type==='email'?'安全团队邮箱':'安全事件 Webhook'} value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label><label className="text-sm"><span className="mb-1.5 block font-medium">{form.channel_type==='email'?'邮箱地址':'Webhook URL'}</span><input required type={form.channel_type==='email'?'email':'url'} className="w-full rounded-md border bg-background px-3 py-2" placeholder={form.channel_type==='email'?'security@example.com':'https://hooks.example.com/security'} value={form.target} onChange={e=>setForm({...form,target:e.target.value})}/></label></div>
      {add.isError && <p className="mt-3 text-sm text-destructive">渠道创建失败，请检查输入或服务配置。</p>}
      <div className="mt-4 flex justify-end"><button disabled={add.isPending} className="rounded-lg bg-primary px-5 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50">{add.isPending?'保存中…':'保存渠道'}</button></div>
    </form>}

    {isLoading ? <div className="rounded-xl border p-8 text-center text-muted-foreground">加载中…</div> : data.length===0 ? <div className="rounded-xl border border-dashed p-10 text-center"><Bell className="mx-auto h-8 w-8 text-muted-foreground"/><p className="mt-3 font-medium">暂无通知渠道</p><p className="mt-1 text-sm text-muted-foreground">创建 Email 或 Webhook 渠道接收风险告警。</p></div> : <div className="grid gap-3 lg:grid-cols-2">{data.map(channel => {const Icon=channel.channel_type==='email'?Mail:Webhook;return <article key={channel.id} className="rounded-xl border bg-card p-4 shadow-sm"><div className="flex items-start justify-between gap-4"><div className="flex min-w-0 gap-3"><span className={`rounded-lg p-2 ${channel.enabled?'bg-primary/10 text-primary':'bg-muted text-muted-foreground'}`}><Icon className="h-5 w-5"/></span><div className="min-w-0"><div className="flex items-center gap-2"><h2 className="truncate font-semibold">{channel.name}</h2><span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${channel.enabled?'bg-emerald-500/10 text-emerald-600':'bg-slate-500/10 text-slate-500'}`}>{channel.enabled?'已启用':'已停用'}</span></div><p className="mt-1 truncate text-xs text-muted-foreground" title={channel.target}>{channel.target}</p></div></div><button title="删除渠道" disabled={remove.isPending} onClick={() => {if(window.confirm(`确定删除通知渠道“${channel.name}”吗？`))remove.mutate(channel.id);}} className="rounded-md p-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"><Trash2 className="h-4 w-4"/></button></div><div className="mt-4 flex items-center justify-between border-t pt-3"><span className="text-xs uppercase text-muted-foreground">{channel.channel_type}</span><label className="flex cursor-pointer items-center gap-2 text-xs text-muted-foreground"><span>{channel.enabled?'启用':'停用'}</span><button type="button" role="switch" aria-checked={channel.enabled} disabled={update.isPending} onClick={() => update.mutate({channel,enabled:!channel.enabled})} className={`relative h-6 w-11 rounded-full transition-colors ${channel.enabled?'bg-emerald-500':'bg-slate-300 dark:bg-slate-600'}`}><span className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${channel.enabled?'translate-x-5':'translate-x-0'}`}/></button></label></div></article>;})}</div>}
  </div>;
};
