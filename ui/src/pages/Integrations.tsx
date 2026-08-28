import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { integrationsApi } from '@/services/api';
import type { IntegrationType, UserIntegration } from '@/types';

type SourceProvider = Extract<IntegrationType, 'github' | 'gitlab' | 'gitee' | 'brave'>;
const CONFIG = {
  github: { name: 'GitHub', placeholder: 'ghp_xxxxxxxxxxxxxxxxxxxx', help: 'Use a token with repository and organization read access.' },
  gitlab: { name: 'GitLab', placeholder: 'glpat-xxxxxxxxxxxxxxxxxxxx', help: 'Use a token with read_api access.' },
  gitee: { name: 'Gitee', placeholder: 'xxxxxxxxxxxxxxxxxxxx', help: 'Use an API v5 personal access token with repository read access.' },
  brave: { name: 'Brave Search', placeholder: 'BSA-xxxxxxxxxxxxxxxxxxxx', help: 'Use an official Brave Search API subscription key.' },
} satisfies Record<SourceProvider, { name: string; placeholder: string; help: string }>;

export const Integrations: React.FC = () => {
  const qc = useQueryClient();
  const { data = [], isLoading } = useQuery({ queryKey: ['integrations'], queryFn: integrationsApi.list });
  const create = useMutation({ mutationFn: integrationsApi.create, onSuccess: () => qc.invalidateQueries({ queryKey: ['integrations'] }) });
  const validate = useMutation({ mutationFn: integrationsApi.validate, onSuccess: () => qc.invalidateQueries({ queryKey: ['integrations'] }) });
  return <div className="max-w-4xl space-y-6">
    <p className="text-sm text-muted-foreground">Connect source APIs used for discovery and scanning.</p>
    {isLoading ? <p>Loading...</p> : (Object.keys(CONFIG) as SourceProvider[]).map(provider => <IntegrationCard
      key={provider} provider={provider} integration={data.find(item => item.provider === provider)}
      busy={create.isPending || validate.isPending}
      onSave={token => create.mutate({ provider, token })} onValidate={id => validate.mutate(id)}
    />)}
  </div>;
};

function IntegrationCard({ provider, integration, busy, onSave, onValidate }: {
  provider: SourceProvider; integration?: UserIntegration; busy: boolean;
  onSave: (token: string) => void; onValidate: (id: number) => void;
}) {
  const [token, setToken] = useState('');
  const [editing, setEditing] = useState(!integration);
  const config = CONFIG[provider];
  const connected = integration?.status === 'connected';
  return <section className="bg-card border rounded-lg p-6 space-y-4">
    <div className="flex justify-between gap-4"><div><h2 className="text-xl font-semibold">{config.name}</h2><p className="text-sm text-muted-foreground">{config.help}</p></div>
      <span className={`px-3 py-1 rounded-full text-sm h-fit ${connected ? 'bg-green-500/10 text-green-600' : 'bg-yellow-500/10 text-yellow-600'}`}>{integration?.status ?? 'not connected'}</span>
    </div>
    {integration?.error_message && <p className="p-3 bg-destructive/10 text-destructive rounded">{integration.error_message}</p>}
    {integration && !editing ? <div className="space-y-3">
      <p className="text-sm text-muted-foreground">Last validated: {integration.last_validated_at ? new Date(integration.last_validated_at).toLocaleString() : 'Never'}</p>
      <div className="flex gap-2"><button disabled={busy} onClick={() => onValidate(integration.id)} className="px-4 py-2 bg-primary text-primary-foreground rounded">Test Connection</button><button onClick={() => setEditing(true)} className="px-4 py-2 border rounded">Update Token</button></div>
    </div> : <form className="space-y-3" onSubmit={event => { event.preventDefault(); onSave(token.trim()); setToken(''); setEditing(false); }}>
      <input type="password" required minLength={10} value={token} onChange={event => setToken(event.target.value)} placeholder={config.placeholder} className="w-full px-3 py-2 border rounded bg-background" />
      <div className="flex gap-2"><button disabled={busy} className="px-4 py-2 bg-primary text-primary-foreground rounded">Save Token</button>{integration && <button type="button" onClick={() => setEditing(false)} className="px-4 py-2 border rounded">Cancel</button>}</div>
    </form>}
  </section>;
}
