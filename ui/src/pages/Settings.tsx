import React, { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Mail, Send } from 'lucide-react';
import { settingsApi, ignoreRulesApi, emailConfigurationApi } from '@/services/api';
import { useSearchParams } from 'react-router-dom';
import { useLanguage } from '@/i18n/LanguageContext';
import { ExcludedRepositories } from '@/pages/ExcludedRepositories';
import type { EmailConfiguration } from '@/types';

export const Settings: React.FC = () => {
  const queryClient = useQueryClient();
  const { t } = useLanguage();
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get('tab') === 'exclusions' ? 'exclusions' : 'system';
  const { data: settings, isLoading: settingsLoading } = useQuery({ queryKey: ['settings'], queryFn: settingsApi.get });
  const { data: ignoreTypes = [], isLoading: typesLoading } = useQuery({ queryKey: ['ignore-types'], queryFn: ignoreRulesApi.listTypes });
  const { data: ignoreDomains = [], isLoading: domainsLoading } = useQuery({ queryKey: ['ignore-domains'], queryFn: ignoreRulesApi.listDomains });
  const { data: savedEmailConfig } = useQuery({ queryKey: ['email-configuration'], queryFn: emailConfigurationApi.get });
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [orgReposOnly, setOrgReposOnly] = useState(false);
  const [brandName, setBrandName] = useState('万联源码泄漏监控');
  const [loginTitle, setLoginTitle] = useState('登录万联源码泄漏监控');
  const [homeTitle, setHomeTitle] = useState('万联源码泄漏监控');
  const [homeDescription, setHomeDescription] = useState('持续监控公开代码平台，发现源码与敏感信息泄漏风险');
  const [emailConfig, setEmailConfig] = useState<Partial<EmailConfiguration>>({ enabled:false, host:'', port:587, username:'', password:'', from_email:'', use_tls:true, use_ssl:false });
  const [newType, setNewType] = useState('');
  const [newDomain, setNewDomain] = useState('');
  useEffect(() => { if (settings) { setVerifiedOnly(settings.verified_only); setOrgReposOnly(settings.org_repos_only); setBrandName(settings.brand_name); setLoginTitle(settings.login_title); setHomeTitle(settings.home_title); setHomeDescription(settings.home_description); } }, [settings]);
  useEffect(() => { if (savedEmailConfig) setEmailConfig({...savedEmailConfig, password:''}); }, [savedEmailConfig]);
  const updateSettingsMutation = useMutation({ mutationFn: settingsApi.update, onSuccess: () => { queryClient.invalidateQueries({queryKey:['settings']}); queryClient.invalidateQueries({queryKey:['branding']}); } });
  const saveEmailMutation = useMutation({ mutationFn: emailConfigurationApi.update, onSuccess: value => { queryClient.setQueryData(['email-configuration'], value); setEmailConfig({...value,password:''}); } });
  const addTypeMutation = useMutation({ mutationFn: ignoreRulesApi.createType, onSuccess: () => { queryClient.invalidateQueries({queryKey:['ignore-types']}); setNewType(''); } });
  const deleteTypeMutation = useMutation({ mutationFn: ignoreRulesApi.deleteType, onSuccess: () => queryClient.invalidateQueries({queryKey:['ignore-types']}) });
  const addDomainMutation = useMutation({ mutationFn: ignoreRulesApi.createDomain, onSuccess: () => { queryClient.invalidateQueries({queryKey:['ignore-domains']}); setNewDomain(''); } });
  const deleteDomainMutation = useMutation({ mutationFn: ignoreRulesApi.deleteDomain, onSuccess: () => queryClient.invalidateQueries({queryKey:['ignore-domains']}) });
  const saveSettings = (e:React.FormEvent) => { e.preventDefault(); updateSettingsMutation.mutate({verified_only:verifiedOnly,org_repos_only:orgReposOnly,brand_name:brandName,login_title:loginTitle,home_title:homeTitle,home_description:homeDescription}); };
  return <div className="space-y-6">
    <div className="flex gap-1 border-b"><button onClick={()=>setSearchParams({tab:'system'})} className={`px-5 py-3 text-sm font-medium ${tab==='system'?'border-b-2 border-primary text-primary':'text-muted-foreground'}`}>{t('System and Ignore Rules')}</button><button onClick={()=>setSearchParams({tab:'exclusions'})} className={`px-5 py-3 text-sm font-medium ${tab==='exclusions'?'border-b-2 border-primary text-primary':'text-muted-foreground'}`}>{t('Excluded Repositories')}</button></div>
    {tab==='exclusions' ? <ExcludedRepositories embedded /> : <div className="space-y-6">
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-xl font-semibold text-foreground mb-4">{t('System Settings')}</h2>
        {settingsLoading ? <div className="text-muted-foreground">{t('Loading...')}</div> : <form onSubmit={saveSettings} className="space-y-5">
          <div className="rounded-lg border bg-muted/20 p-4"><h3 className="mb-3 font-semibold">{t('Branding')}</h3><div className="grid gap-4 md:grid-cols-2">
            {[[t('Brand Name'),brandName,setBrandName,120],[t('Login Page Title'),loginTitle,setLoginTitle,160],[t('Home Page Title'),homeTitle,setHomeTitle,160],[t('Home Page Description'),homeDescription,setHomeDescription,500]].map(([label,value,setter,max])=><label key={String(label)} className="text-sm"><span className="mb-1 block font-medium">{label as string}</span><input required maxLength={max as number} value={value as string} onChange={e=>(setter as React.Dispatch<React.SetStateAction<string>>)(e.target.value)} className="w-full rounded-md border bg-background px-3 py-2" /></label>)}
          </div></div>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={verifiedOnly} onChange={e=>setVerifiedOnly(e.target.checked)}/><span className="font-medium">{t('Verified Secrets Only')}</span></label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={orgReposOnly} onChange={e=>setOrgReposOnly(e.target.checked)}/><span className="font-medium">{t('Organization Repositories Only')}</span></label>
          <button disabled={updateSettingsMutation.isPending} className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">{updateSettingsMutation.isPending?t('Saving...'):t('Save Settings')}</button>
        </form>}
      </div>
      <form onSubmit={e=>{e.preventDefault();saveEmailMutation.mutate(emailConfig)}} className="bg-card border border-border rounded-lg p-6"><div className="mb-4 flex items-start justify-between"><div className="flex gap-3"><span className="rounded-lg bg-primary/10 p-2 text-primary"><Mail className="h-5 w-5"/></span><div><h2 className="text-lg font-semibold">{t('Email Sender')}</h2><p className="text-sm text-muted-foreground">{t('Configure the SMTP account and sender used by all Email channels.')}</p></div></div><button type="button" role="switch" aria-checked={!!emailConfig.enabled} onClick={()=>setEmailConfig({...emailConfig,enabled:!emailConfig.enabled})} className={`relative h-6 w-11 rounded-full ${emailConfig.enabled?'bg-emerald-500':'bg-muted'}`}><span className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${emailConfig.enabled?'translate-x-5':''}`}/></button></div><div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <label className="text-sm"><span className="mb-1 block font-medium">{t('SMTP Server')}</span><input required={emailConfig.enabled} value={emailConfig.host||''} onChange={e=>setEmailConfig({...emailConfig,host:e.target.value})} className="w-full rounded-md border bg-background px-3 py-2" placeholder="smtp.example.com"/></label>
        <label className="text-sm"><span className="mb-1 block font-medium">{t('SMTP Port')}</span><input required type="number" min="1" max="65535" value={emailConfig.port||587} onChange={e=>setEmailConfig({...emailConfig,port:Number(e.target.value)})} className="w-full rounded-md border bg-background px-3 py-2"/></label>
        <label className="text-sm"><span className="mb-1 block font-medium">{t('Sender Address')}</span><input required={emailConfig.enabled} type="email" value={emailConfig.from_email||''} onChange={e=>setEmailConfig({...emailConfig,from_email:e.target.value})} className="w-full rounded-md border bg-background px-3 py-2"/></label>
        <label className="text-sm"><span className="mb-1 block font-medium">{t('SMTP Username')}</span><input value={emailConfig.username||''} onChange={e=>setEmailConfig({...emailConfig,username:e.target.value})} className="w-full rounded-md border bg-background px-3 py-2"/></label>
        <label className="text-sm"><span className="mb-1 block font-medium">{t('SMTP Password')}</span><input type="password" value={emailConfig.password||''} onChange={e=>setEmailConfig({...emailConfig,password:e.target.value})} placeholder={emailConfig.password_configured?t('Keep current encrypted password'):t('Enter SMTP password')} className="w-full rounded-md border bg-background px-3 py-2"/></label>
        <div className="flex items-end gap-4 pb-2 text-sm"><label className="flex items-center gap-2"><input type="checkbox" checked={!!emailConfig.use_tls} onChange={e=>setEmailConfig({...emailConfig,use_tls:e.target.checked,use_ssl:e.target.checked?false:emailConfig.use_ssl})}/>{t('STARTTLS')}</label><label className="flex items-center gap-2"><input type="checkbox" checked={!!emailConfig.use_ssl} onChange={e=>setEmailConfig({...emailConfig,use_ssl:e.target.checked,use_tls:e.target.checked?false:emailConfig.use_tls})}/>{t('SSL')}</label></div>
      </div><div className="mt-4 flex justify-end"><button disabled={saveEmailMutation.isPending} className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2 text-sm font-medium text-primary-foreground"><Send className="h-4 w-4"/>{saveEmailMutation.isPending?t('Saving...'):t('Save Email Sender')}</button></div></form>
      <div className="bg-card border border-border rounded-lg p-6"><h2 className="text-xl font-semibold mb-4">{t('Ignore Finding Types')}</h2><form onSubmit={e=>{e.preventDefault();if(newType.trim())addTypeMutation.mutate({type:newType.trim()})}} className="flex gap-2 mb-4"><input value={newType} onChange={e=>setNewType(e.target.value)} placeholder={t('Enter detector type to ignore')} className="flex-1 rounded-md border bg-background px-3 py-2"/><button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">{t('Add')}</button></form>{typesLoading?<p>{t('Loading...')}</p>:ignoreTypes.length===0?<p className="rounded-lg bg-muted p-4 text-center text-sm text-muted-foreground">{t('No ignored types yet')}</p>:<div className="space-y-2">{ignoreTypes.map(type=><div key={type.id} className="flex items-center justify-between rounded-lg bg-muted p-3"><span className="text-sm font-medium">{type.type}</span><button onClick={()=>deleteTypeMutation.mutate(type.id)} className="text-sm text-destructive">{t('Remove')}</button></div>)}</div>}</div>
      <div className="bg-card border border-border rounded-lg p-6"><h2 className="text-xl font-semibold mb-4">{t('Ignore Email Domains')}</h2><form onSubmit={e=>{e.preventDefault();if(newDomain.trim())addDomainMutation.mutate({domain:newDomain.trim()})}} className="flex gap-2 mb-4"><input value={newDomain} onChange={e=>setNewDomain(e.target.value)} placeholder="example.org" className="flex-1 rounded-md border bg-background px-3 py-2"/><button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">{t('Add')}</button></form>{domainsLoading?<p>{t('Loading...')}</p>:ignoreDomains.length===0?<p className="rounded-lg bg-muted p-4 text-center text-sm text-muted-foreground">{t('No ignored domains yet')}</p>:<div className="space-y-2">{ignoreDomains.map(domain=><div key={domain.id} className="flex items-center justify-between rounded-lg bg-muted p-3"><span className="text-sm font-medium">{domain.domain}</span><button onClick={()=>deleteDomainMutation.mutate(domain.id)} className="text-sm text-destructive">{t('Remove')}</button></div>)}</div>}</div>
    </div>}
  </div>;
};
