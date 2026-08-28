import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { excludedRepositoriesApi, scansApi } from '@/services/api';
import type { ScanRepository } from '@/types';

export const ScanDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: scan, isLoading, error } = useQuery({
    queryKey: ['scan', id],
    queryFn: () => scansApi.get(Number(id)),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Auto-refresh every 3 seconds if scan is active
      const isActive = data?.execution_status === 'QUEUED' || data?.execution_status === 'RUNNING';
      return isActive ? 3000 : false;
    },
  });

  const { data: repositories = [] } = useQuery({
    queryKey: ['scan-repositories', id],
    queryFn: () => scansApi.getRepositories(Number(id)),
    enabled: !!id,
    refetchInterval: scan?.execution_status === 'RUNNING' ? 3000 : false,
  });

  const excludeRepositoryMutation = useMutation({
    mutationFn: ({ repository, reason }: { repository: ScanRepository; reason: string }) => excludedRepositoriesApi.create({
      source: repository.source,
      repository_url: repository.repository_url,
      owner: repository.owner,
      repository: repository.repository,
      reason,
      enabled: true,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scan-repositories', id] });
      queryClient.invalidateQueries({ queryKey: ['excluded-repositories'] });
    },
  });

  const deleteScanMutation = useMutation({
    mutationFn: scansApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] });
      navigate('/scans');
    },
  });

  const handleDeleteScan = () => {
    if (scan && window.confirm(`Are you sure you want to delete the scan "${scan.value}"? This action cannot be undone.`)) {
      deleteScanMutation.mutate(scan.id);
    }
  };

  const handleExcludeRepository = (repository: ScanRepository) => {
    const reason = window.prompt('Reason for permanently excluding this repository:', 'Not in monitoring scope');
    if (reason === null) return;
    if (window.confirm(`Permanently exclude ${repository.repository_url} from future scans? Historical scans and findings will be retained.`)) {
      excludeRepositoryMutation.mutate({ repository, reason: reason.trim() });
    }
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      QUEUED: 'bg-blue-500/10 text-blue-600',
      RUNNING: 'bg-yellow-500/10 text-yellow-600',
      SUCCESS: 'bg-green-500/10 text-green-600',
      DEGRADED: 'bg-orange-500/10 text-orange-600',
      FAILED: 'bg-red-500/10 text-red-600',
    };
    return styles[status as keyof typeof styles] || 'bg-gray-500/10 text-gray-600';
  };

  const formatScanType = (type: string) => {
    const typeMap: Record<string, string> = {
      org_repos: 'Organization Repositories',
      org_users: 'Organization Users',
      search_code: 'Search Code',
      search_commits: 'Search Commits',
      search_issues: 'Search Issues',
      search_repos: 'Search Repositories',
      search_users: 'Search Users',
    };
    return typeMap[type] || type;
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="bg-card border border-border rounded-lg p-8 text-center">
          <p className="text-muted-foreground">Loading scan details...</p>
        </div>
      </div>
    );
  }

  if (error || !scan) {
    return (
      <div className="space-y-6">
        <div className="bg-card border border-border rounded-lg p-8 text-center">
          <p className="text-destructive">Failed to load scan details</p>
          <Link
            to="/scans?tab=history"
            className="inline-block mt-4 text-primary hover:underline"
          >
            Back to Scans
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Link
              to="/scans?tab=history"
              className="text-muted-foreground hover:text-foreground"
            >
              ← Back
            </Link>
            <h1 className="text-3xl font-bold text-foreground">Scan Details</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">Scan #{scan.id}</p>
        </div>
        <div className="flex gap-2">
          <Link
            to={`/findings?scan=${scan.id}`}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90 transition-opacity"
          >
            View Findings
          </Link>
          <button
            onClick={handleDeleteScan}
            disabled={deleteScanMutation.isPending}
            className="px-4 py-2 bg-destructive text-destructive-foreground rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {deleteScanMutation.isPending ? 'Deleting...' : 'Delete Scan'}
          </button>
        </div>
      </div>

      <div className="bg-card border border-border rounded-lg p-6 space-y-6">
        {/* Basic Information */}
        <div>
          <h2 className="text-xl font-semibold text-foreground mb-4">Basic Information</h2>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Scan Type</h3>
              <p className="text-foreground text-lg">{formatScanType(scan.type)}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Status</h3>
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(scan.execution_status)}`}
              >
                {scan.execution_status}
              </span>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Monitoring Status</h3>
              <p className="text-foreground text-lg">{scan.monitoring_status}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Result Status</h3>
              <p className="text-foreground text-lg">{scan.result_status || '—'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Query/Value</h3>
              <p className="text-foreground text-lg font-mono">{scan.value}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">User</h3>
              <p className="text-foreground text-lg">{scan.user}</p>
            </div>
          </div>
        </div>

        {(scan.error_code || scan.error_message) && (
          <div className="border-t border-border pt-6">
            <h2 className="text-xl font-semibold text-destructive mb-2">Execution Error</h2>
            <p className="font-mono text-sm text-foreground">{scan.error_code}</p>
            <p className="text-sm text-muted-foreground mt-1">{scan.error_message}</p>
          </div>
        )}

        {/* Statistics */}
        <div className="border-t border-border pt-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="bg-muted p-4 rounded-lg">
              <h3 className="text-sm font-medium text-muted-foreground mb-1">Total Repositories</h3>
              <p className="text-3xl font-bold text-foreground">{scan.total_repositories}</p>
            </div>
            <div className="bg-muted p-4 rounded-lg">
              <h3 className="text-sm font-medium text-muted-foreground mb-1">Scanned</h3>
              <p className="text-3xl font-bold text-foreground">{scan.scanned_repositories}</p>
            </div>
            <div className="bg-muted p-4 rounded-lg">
              <h3 className="text-sm font-medium text-muted-foreground mb-1">Total Findings</h3>
              <p className="text-3xl font-bold text-foreground">{scan.total_findings}</p>
            </div>
            <div className="bg-muted p-4 rounded-lg">
              <h3 className="text-sm font-medium text-muted-foreground mb-1">Ignored</h3>
              <p className="text-3xl font-bold text-muted-foreground">
                {scan.ignored_repositories + scan.ignored_findings}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {scan.ignored_repositories} repos, {scan.ignored_findings} findings
              </p>
            </div>
          </div>
        </div>

        {/* Timestamps */}
        <div className="border-t border-border pt-6">
          <div className="flex items-center justify-between mb-4">
            <div><h2 className="text-xl font-semibold text-foreground">Repositories</h2><p className="text-sm text-muted-foreground">Repositories discovered by this query and their scan disposition.</p></div>
            <Link to="/excluded-repositories" className="text-sm text-primary hover:underline">Manage exclusions</Link>
          </div>
          {repositories.length === 0 ? <p className="text-sm text-muted-foreground">No repositories discovered.</p> : (
            <div className="overflow-x-auto border rounded-lg"><table className="w-full text-sm"><thead className="bg-muted"><tr><th className="text-left p-3">Repository</th><th className="text-left p-3">Source</th><th className="text-left p-3">Status</th><th className="text-right p-3">Findings</th><th className="text-right p-3">Action</th></tr></thead><tbody className="divide-y">{repositories.map(repository => <tr key={repository.id}>
              <td className="p-3"><a href={repository.repository_url} target="_blank" rel="noreferrer" className="font-medium text-primary hover:underline">{repository.owner ? `${repository.owner}/${repository.repository}` : repository.repository_url}</a>{repository.error_message && <p className="text-xs text-destructive mt-1">{repository.error_message}</p>}</td>
              <td className="p-3 uppercase text-xs">{repository.source}</td>
              <td className="p-3"><span className={`px-2 py-1 rounded-full text-xs font-medium ${repository.status === 'COMPLETED' ? 'bg-green-500/10 text-green-600' : repository.status === 'EXCLUDED' ? 'bg-slate-500/10 text-slate-600' : repository.status === 'FAILED' ? 'bg-red-500/10 text-red-600' : repository.status === 'DEGRADED' ? 'bg-orange-500/10 text-orange-600' : 'bg-blue-500/10 text-blue-600'}`}>{repository.status}</span></td>
              <td className="p-3 text-right">{repository.findings_count}</td>
              <td className="p-3 text-right">{repository.is_permanently_excluded ? <span className="text-xs text-muted-foreground">Permanently excluded</span> : <button disabled={excludeRepositoryMutation.isPending} onClick={() => handleExcludeRepository(repository)} className="text-destructive hover:underline">Exclude permanently</button>}</td>
            </tr>)}</tbody></table></div>
          )}
        </div>

        {/* Timestamps */}
        <div className="border-t border-border pt-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">Timeline</h2>
          <div className="grid grid-cols-3 gap-6">
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Created At</h3>
              <p className="text-foreground">{new Date(scan.created_at).toLocaleString()}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Updated At</h3>
              <p className="text-foreground">{new Date(scan.updated_at).toLocaleString()}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Completed At</h3>
              <p className="text-foreground">
                {scan.completed_at ? new Date(scan.completed_at).toLocaleString() : 'Not completed'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
