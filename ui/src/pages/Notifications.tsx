import React, { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Bell, Mail, Plus, Send, Server, Trash2, Webhook } from 'lucide-react';
import { emailConfigurationApi, notificationChannelsApi } from '@/services/api';
import type { EmailConfiguration, NotificationChannel } from '@/types';

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
  const { data: savedEmailConfig } = useQuery({ queryKey:['email-configuration'], queryFn:emailConfigurationApi.get });
  const [emailConfig, setEmailConfig] = useState<Partial<EmailConfiguration>>({ enabled:false, host:'', port:587, username:'', password:'', from_email:'', use_tls:true, use_ssl:false });
  useEffect(() => { if (savedEmailConfig) setEmailConfig({...savedEmailConfig,password:''}); }, [savedEmailConfig]);
  const saveEmailConfig = useMutation({
    mutationFn:emailConfigurationApi.update,
    onSuccess:(value) => { qc.setQueryData(['email-configuration'], value); setEmailConfig({...value,password:''}); },
  });

  return <div className="space-y-5">
    <form className="rounded-xl border bg-card p-5 shadow-sm" onSubmit={event => { event.preventDefault(); saveEmailConfig.mutate(emailConfig); }}>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3"><div className="flex gap-3"><span className="rounded-lg bg-primary/10 p-2 text-primary"><Server className="h-5 w-5"/></span><div><h2 className="font-semibold">Email Sender</h2><p className="text-sm text-muted-foreground">Configure the SMTP account and sender used by all Email channels.</p></div></div><label className="flex items-center gap-2 text-sm"><span>{emailConfig.enabled?'Enabled':'Disabled'}</span><button type="button" role="switch" aria-checked={emailConfig.enabled} onClick={() => setEmailConfig({...emailConfig,enabled:!emailConfig.enabled})} className={`relative h-6 w-11 rounded-full ${emailConfig.enabled?'bg-emerald-500':'bg-slate-300 dark:bg-slate-600'}`}><span className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${emailConfig.enabled?'translate-x-5':''}`}/></button></label></div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <label className="text-sm"><span className="mb-1.5 block font-medium">SMTP Server</span><input required={emailConfig.enabled} value={emailConfig.host||''} onChange={e=>setEmailConfig({...emailConfig,host:e.target.value})} placeholder="smtp.example.com" className="w-full rounded-md border bg-background px-3 py-2"/></label>
        <label className="text-sm"><span className="mb-1.5 block font-medium">SMTP Port</span><input required type="number" min="1" max="65535" value={emailConfig.port||587} onChange={e=>setEmailConfig({...emailConfig,port:Number(e.target.value)})} className="w-full rounded-md border bg-background px-3 py-2"/></label>
        <label className="text-sm"><span className="mb-1.5 block font-medium">Sender Address</span><input required={emailConfig.enabled} type="email" value={emailConfig.from_email||''} onChange={e=>setEmailConfig({...emailConfig,from_email:e.target.value})} placeholder="alerts@example.com" className="w-full rounded-md border bg-background px-3 py-2"/></label>
        <label className="text-sm"><span className="mb-1.5 block font-medium">SMTP Username</span><input value={emailConfig.username||''} onChange={e=>setEmailConfig({...emailConfig,username:e.target.value})} autoComplete="username" className="w-full rounded-md border bg-background px-3 py-2"/></label>
        <label className="text-sm"><span className="mb-1.5 block font-medium">SMTP Password</span><input type="password" value={emailConfig.password||''} onChange={e=>setEmailConfig({...emailConfig,password:e.target.value})} autoComplete="new-password" placeholder={emailConfig.password_configured?'Keep current encrypted password':'Enter SMTP password'} className="w-full rounded-md border bg-background px-3 py-2"/></label>
        <div className="flex items-end gap-5 pb-2 text-sm"><label className="flex items-center gap-2"><input type="checkbox" checked={!!emailConfig.use_tls} onChange={e=>setEmailConfig({...emailConfig,use_tls:e.target.checked,use_ssl:e.target.checked?false:emailConfig.use_ssl})}/>STARTTLS</label><label className="flex items-center gap-2"><input type="checkbox" checked={!!emailConfig.use_ssl} onChange={e=>setEmailConfig({...emailConfig,use_ssl:e.target.checked,use_tls:e.target.checked?false:emailConfig.use_tls})}/>SSL</label></div>
      </div>
      {saveEmailConfig.isError && <p className="mt-3 text-sm text-destructive">Failed to save Email sender settings.</p>}
      {saveEmailConfig.isSuccess && <p className="mt-3 text-sm text-emerald-600">Email sender settings saved.</p>}
      <div className="mt-4 flex justify-end"><button disabled={saveEmailConfig.isPending} className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"><Send className="h-4 w-4"/>{saveEmailConfig.isPending?'Saving...':'Save Email Sender'}</button></div>
    </form>
    <div className="flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-2 text-sm text-muted-foreground"><Bell className="h-4 w-4"/><span>CRITICAL/HIGH are sent immediately; only NEW and REOPENED Findings are notified by default.</span></div><button onClick={() => setShowForm(!showForm)} className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"><Plus className="h-4 w-4"/>{showForm ? 'Collapse' : 'Add Notification Channel'}</button></div>

    {showForm && <form className="rounded-xl border bg-card p-5 shadow-sm" onSubmit={event => {event.preventDefault();add.mutate(form);}}>
      <div className="mb-4 grid gap-3 sm:grid-cols-2">
        {(['email','webhook'] as const).map(type => { const Icon=type==='email'?Mail:Webhook; return <button type="button" key={type} onClick={() => setForm({...form,channel_type:type,target:''})} className={`flex items-center gap-3 rounded-lg border p-3 text-left ${form.channel_type===type?'border-primary bg-primary/5':''}`}><span className={`rounded-lg p-2 ${form.channel_type===type?'bg-primary/10 text-primary':'bg-muted text-muted-foreground'}`}><Icon className="h-5 w-5"/></span><span><strong className="block text-sm">{type==='email'?'Email':'Webhook'}</strong><small className="text-muted-foreground">{type==='email'?'Send to the security team mailbox':'Push to an HTTPS endpoint'}</small></span></button>;})}
      </div>
      <div className="grid gap-4 md:grid-cols-2"><label className="text-sm"><span className="mb-1.5 block font-medium">Channel Name</span><input required className="w-full rounded-md border bg-background px-3 py-2" placeholder={form.channel_type==='email'?'Security team mailbox':'Security event Webhook'} value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label><label className="text-sm"><span className="mb-1.5 block font-medium">{form.channel_type==='email'?'Email Address':'Webhook URL'}</span><input required type={form.channel_type==='email'?'email':'url'} className="w-full rounded-md border bg-background px-3 py-2" placeholder={form.channel_type==='email'?'security@example.com':'https://hooks.example.com/security'} value={form.target} onChange={e=>setForm({...form,target:e.target.value})}/></label></div>
      {add.isError && <p className="mt-3 text-sm text-destructive">Failed to create channel. Check the input and service configuration.</p>}
      <div className="mt-4 flex justify-end"><button disabled={add.isPending} className="rounded-lg bg-primary px-5 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50">{add.isPending?'Saving...':'Save Channel'}</button></div>
    </form>}

    {isLoading ? <div className="rounded-xl border p-8 text-center text-muted-foreground">Loading...</div> : data.length===0 ? <div className="rounded-xl border border-dashed p-10 text-center"><Bell className="mx-auto h-8 w-8 text-muted-foreground"/><p className="mt-3 font-medium">No notification channels</p><p className="mt-1 text-sm text-muted-foreground">Create an Email or Webhook channel to receive risk alerts.</p></div> : <div className="grid gap-3 lg:grid-cols-2">{data.map(channel => {const Icon=channel.channel_type==='email'?Mail:Webhook;return <article key={channel.id} className="rounded-xl border bg-card p-4 shadow-sm"><div className="flex items-start justify-between gap-4"><div className="flex min-w-0 gap-3"><span className={`rounded-lg p-2 ${channel.enabled?'bg-primary/10 text-primary':'bg-muted text-muted-foreground'}`}><Icon className="h-5 w-5"/></span><div className="min-w-0"><div className="flex items-center gap-2"><h2 className="truncate font-semibold">{channel.name}</h2><span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${channel.enabled?'bg-emerald-500/10 text-emerald-600':'bg-slate-500/10 text-slate-500'}`}>{channel.enabled?'Enabled':'Disabled'}</span></div><p className="mt-1 truncate text-xs text-muted-foreground" title={channel.target}>{channel.target}</p></div></div><button title="Delete Channel" disabled={remove.isPending} onClick={() => {if(window.confirm(`Delete notification channel "${channel.name}"?`))remove.mutate(channel.id);}} className="rounded-md p-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"><Trash2 className="h-4 w-4"/></button></div><div className="mt-4 flex items-center justify-between border-t pt-3"><span className="text-xs uppercase text-muted-foreground">{channel.channel_type}</span><label className="flex cursor-pointer items-center gap-2 text-xs text-muted-foreground"><span>{channel.enabled?'Enable':'Disable'}</span><button type="button" role="switch" aria-checked={channel.enabled} disabled={update.isPending} onClick={() => update.mutate({channel,enabled:!channel.enabled})} className={`relative h-6 w-11 rounded-full transition-colors ${channel.enabled?'bg-emerald-500':'bg-slate-300 dark:bg-slate-600'}`}><span className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${channel.enabled?'translate-x-5':'translate-x-0'}`}/></button></label></div></article>;})}</div>}
  </div>;
};
