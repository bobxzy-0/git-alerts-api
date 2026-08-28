import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { integrationsApi } from '@/services/api';
import type { IntegrationType, UserIntegration } from '@/types';

type SourceProvider = Extract<IntegrationType, 'github' | 'gitlab' | 'gitee' | 'you'>;
type ProxyMode = 'keep' | 'none' | 'configure';
type ProxyScheme = 'http' | 'https' | 'socks5';
const CONFIG = {
  github: { name: 'GitHub', placeholder: 'ghp_xxxxxxxxxxxxxxxxxxxx', help: 'Use a token with repository and organization read access.' },
  gitlab: { name: 'GitLab', placeholder: 'glpat-xxxxxxxxxxxxxxxxxxxx', help: 'Use a token with read_api access.' },
  gitee: { name: 'Gitee', placeholder: 'xxxxxxxxxxxxxxxxxxxx', help: 'Use an API v5 personal access token with repository read access.' },
  you: { name: 'You.com Search', placeholder: 'xxxxxxxxxxxxxxxxxxxx', help: 'Use an API key created at you.com/platform/api-keys.' },
} satisfies Record<SourceProvider, { name: string; placeholder: string; help: string }>;

export const Integrations: React.FC = () => {
  const qc = useQueryClient();
  const { data = [], isLoading } = useQuery({ queryKey: ['integrations'], queryFn: integrationsApi.list, refetchInterval: 1_500, refetchIntervalInBackground: false, refetchOnWindowFocus: true });
  const create = useMutation({ mutationFn: integrationsApi.create, onSuccess: () => qc.invalidateQueries({ queryKey: ['integrations'] }) });
  const validate = useMutation({
    mutationFn: integrationsApi.validate,
    onMutate: (id) => qc.setQueryData<UserIntegration[]>(['integrations'], current => current?.map(item => item.id === id ? {...item,status:'pending',error_message:''} : item)),
    onSettled: () => qc.invalidateQueries({ queryKey: ['integrations'] }),
  });
  return <div className="max-w-4xl space-y-6">
    <p className="text-sm text-muted-foreground">Connect source APIs used for discovery and scanning.</p>
    {isLoading ? <p>Loading...</p> : (Object.keys(CONFIG) as SourceProvider[]).map(provider => <IntegrationCard
      key={provider} provider={provider} integration={data.find(item => item.provider === provider)}
      busy={create.isPending || validate.isPending}
      onSave={(token, proxyUrl) => create.mutate({ provider, token, ...(proxyUrl === undefined ? {} : { proxy_url: proxyUrl }) })}
      onValidate={id => validate.mutate(id)}
    />)}
  </div>;
};

function IntegrationCard({ provider, integration, busy, onSave, onValidate }: {
  provider: SourceProvider; integration?: UserIntegration; busy: boolean;
  onSave: (token: string, proxyUrl?: string) => void; onValidate: (id: number) => void;
}) {
  const [token, setToken] = useState('');
  const [editing, setEditing] = useState(!integration);
  const [proxyMode, setProxyMode] = useState<ProxyMode>(integration?.proxy_configured ? 'keep' : 'none');
  const [proxyScheme, setProxyScheme] = useState<ProxyScheme>('http');
  const [proxyHost, setProxyHost] = useState('');
  const [proxyPort, setProxyPort] = useState('');
  const [proxyUsername, setProxyUsername] = useState('');
  const [proxyPassword, setProxyPassword] = useState('');
  const config = CONFIG[provider];
  const connected = integration?.status === 'connected';
  return <section className="bg-card border rounded-lg p-6 space-y-4">
    <div className="flex justify-between gap-4"><div><h2 className="text-xl font-semibold">{config.name}</h2><p className="text-sm text-muted-foreground">{config.help}</p></div>
      <span className={`px-3 py-1 rounded-full text-sm h-fit ${connected ? 'bg-green-500/10 text-green-600' : integration?.status === 'pending' ? 'bg-blue-500/10 text-blue-600' : 'bg-yellow-500/10 text-yellow-600'}`}>{integration?.status ?? 'not connected'}</span>
    </div>
    {integration?.error_message && <p className="p-3 bg-destructive/10 text-destructive rounded">{integration.error_message}</p>}
    {integration && !editing ? <div className="space-y-3">
      <p className="text-sm text-muted-foreground">Last validated: {integration.last_validated_at ? new Date(integration.last_validated_at).toLocaleString() : 'Never'}</p>
      <p className="text-sm">Proxy: {integration.proxy_configured ? <span className="font-medium">{integration.proxy_scheme.toUpperCase()} configured · credentials encrypted</span> : <span className="text-muted-foreground">Direct connection</span>}</p>
      <div className="flex gap-2"><button disabled={busy} onClick={() => onValidate(integration.id)} className="px-4 py-2 bg-primary text-primary-foreground rounded">Test Connection</button><button onClick={() => setEditing(true)} className="px-4 py-2 border rounded">Update Connection</button></div>
    </div> : <form className="space-y-4" onSubmit={event => {
      event.preventDefault();
      let proxyUrl: string | undefined;
      if (proxyMode === 'none') proxyUrl = '';
      if (proxyMode === 'configure') {
        const auth = proxyUsername ? `${encodeURIComponent(proxyUsername)}${proxyPassword ? `:${encodeURIComponent(proxyPassword)}` : ''}@` : '';
        proxyUrl = `${proxyScheme}://${auth}${proxyHost.trim()}:${proxyPort}`;
      }
      onSave(token.trim(), proxyUrl); setToken(''); setEditing(false);
    }}>
      <input type="password" required={!integration} minLength={token ? 10 : undefined} value={token} onChange={event => setToken(event.target.value)} placeholder={integration ? 'Leave blank to keep current encrypted key' : config.placeholder} className="w-full px-3 py-2 border rounded bg-background" />
      {integration && <p className="-mt-2 text-xs text-muted-foreground">The API key is optional when only changing proxy settings.</p>}
      <div className="rounded-lg border bg-muted/20 p-4 space-y-3">
        <div><h3 className="font-medium">Source proxy</h3><p className="text-xs text-muted-foreground">Used by this source's API requests and repository scans. HTTP, HTTPS and SOCKS5 are supported.</p></div>
        <select value={proxyMode} onChange={event => setProxyMode(event.target.value as ProxyMode)} className="w-full px-3 py-2 border rounded bg-background">
          {integration?.proxy_configured && <option value="keep">Keep current encrypted proxy</option>}
          <option value="none">Connect directly (no proxy)</option>
          <option value="configure">Configure or replace proxy</option>
        </select>
        {proxyMode === 'configure' && <div className="grid gap-3 sm:grid-cols-6">
          <select value={proxyScheme} onChange={event => setProxyScheme(event.target.value as ProxyScheme)} className="sm:col-span-2 px-3 py-2 border rounded bg-background"><option value="http">HTTP</option><option value="https">HTTPS</option><option value="socks5">SOCKS5</option></select>
          <input required value={proxyHost} onChange={event => setProxyHost(event.target.value)} placeholder="Proxy host" className="sm:col-span-3 px-3 py-2 border rounded bg-background" />
          <input required type="number" min="1" max="65535" value={proxyPort} onChange={event => setProxyPort(event.target.value)} placeholder="Port" className="px-3 py-2 border rounded bg-background" />
          <input value={proxyUsername} onChange={event => setProxyUsername(event.target.value)} placeholder="Username (optional)" className="sm:col-span-3 px-3 py-2 border rounded bg-background" />
          <input type="password" value={proxyPassword} onChange={event => setProxyPassword(event.target.value)} placeholder="Password (optional)" className="sm:col-span-3 px-3 py-2 border rounded bg-background" />
        </div>}
      </div>
      <div className="flex gap-2"><button disabled={busy} className="px-4 py-2 bg-primary text-primary-foreground rounded">Save Connection</button>{integration && <button type="button" onClick={() => setEditing(false)} className="px-4 py-2 border rounded">Cancel</button>}</div>
    </form>}
  </section>;
}
