import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { excludedRepositoriesApi } from '@/services/api';
import type { ExcludedRepository, SourceType } from '@/types';

function repositoryParts(value: string) {
  try {
    const parts = new URL(value).pathname.split('/').filter(Boolean);
    return { owner: parts.length > 2 ? parts.slice(0, -1).join('/') : parts[0] || '', repository: (parts.at(-1) || '').replace(/\.git$/, '') };
  } catch {
    return { owner: '', repository: '' };
  }
}

export const ExcludedRepositories: React.FC = () => {
  const qc = useQueryClient();
  const { data = [], isLoading } = useQuery({ queryKey: ['excluded-repositories'], queryFn: excludedRepositoriesApi.list });
  const [form, setForm] = useState({ source: 'github' as SourceType, repository_url: '', reason: '' });
  const create = useMutation({
    mutationFn: excludedRepositoriesApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['excluded-repositories'] }); setForm({ ...form, repository_url: '', reason: '' }); },
  });
  const update = useMutation({ mutationFn: ({ item, enabled }: { item: ExcludedRepository; enabled: boolean }) => excludedRepositoriesApi.update(item.id, { enabled }), onSuccess: () => qc.invalidateQueries({ queryKey: ['excluded-repositories'] }) });
  const remove = useMutation({ mutationFn: excludedRepositoriesApi.delete, onSuccess: () => qc.invalidateQueries({ queryKey: ['excluded-repositories'] }) });

  return <div className="space-y-6">
    <div><h1 className="text-3xl font-bold">Excluded Repositories</h1><p className="text-muted-foreground mt-2">Permanently skip exact repositories before any detection engine runs. Historical scans and findings are retained.</p></div>
    <form className="grid md:grid-cols-4 gap-3 border rounded-lg p-4 bg-card" onSubmit={event => { event.preventDefault(); const parts = repositoryParts(form.repository_url); create.mutate({ ...form, ...parts, enabled: true }); }}>
      <select value={form.source} onChange={event => setForm({ ...form, source: event.target.value as SourceType })} className="border rounded px-3 py-2 bg-background"><option value="github">GitHub</option><option value="gitlab">GitLab</option><option value="gitee">Gitee</option><option value="bitbucket">Bitbucket</option><option value="codeberg">Codeberg</option></select>
      <input type="url" required placeholder="https://github.com/owner/repository" value={form.repository_url} onChange={event => setForm({ ...form, repository_url: event.target.value })} className="border rounded px-3 py-2 md:col-span-2" />
      <input placeholder="Reason (optional)" value={form.reason} onChange={event => setForm({ ...form, reason: event.target.value })} className="border rounded px-3 py-2" />
      <button disabled={create.isPending} className="bg-primary text-primary-foreground rounded px-4 py-2 md:col-start-4">{create.isPending ? 'Adding...' : 'Exclude Repository'}</button>
    </form>
    {create.isError && <p className="p-3 rounded bg-destructive/10 text-destructive">The repository could not be excluded. It may already exist in the list.</p>}
    <div className="border rounded-lg bg-card overflow-x-auto">
      {isLoading ? <p className="p-4">Loading...</p> : data.length === 0 ? <p className="p-6 text-center text-muted-foreground">No permanently excluded repositories.</p> : <table className="w-full text-sm"><thead className="bg-muted"><tr><th className="text-left p-3">Repository</th><th className="text-left p-3">Source</th><th className="text-left p-3">Reason</th><th className="text-left p-3">Status</th><th className="text-right p-3">Actions</th></tr></thead><tbody className="divide-y">{data.map(item => <tr key={item.id} className={!item.enabled ? 'opacity-60' : ''}>
        <td className="p-3"><a href={item.repository_url} target="_blank" rel="noreferrer" className="font-medium text-primary hover:underline">{item.owner && item.repository ? `${item.owner}/${item.repository}` : item.repository_url}</a><p className="text-xs text-muted-foreground mt-1 font-mono">{item.normalized_url}</p></td>
        <td className="p-3 uppercase text-xs">{item.source}</td><td className="p-3">{item.reason || '—'}</td><td className="p-3">{item.enabled ? 'ENABLED' : 'DISABLED'}</td>
        <td className="p-3 text-right space-x-3"><button onClick={() => update.mutate({ item, enabled: !item.enabled })} className="text-primary hover:underline">{item.enabled ? 'Disable' : 'Enable'}</button><button onClick={() => { if (window.confirm(`Remove exclusion for ${item.repository_url}?`)) remove.mutate(item.id); }} className="text-destructive hover:underline">Delete</button></td>
      </tr>)}</tbody></table>}
    </div>
  </div>;
};
