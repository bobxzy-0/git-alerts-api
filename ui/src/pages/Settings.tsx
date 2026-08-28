import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsApi, ignoreRulesApi } from '@/services/api';
import { useSearchParams } from 'react-router-dom';
import { ExcludedRepositories } from '@/pages/ExcludedRepositories';

export const Settings: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get('tab') === 'exclusions' ? 'exclusions' : 'system';

  // Fetch system settings
  const { data: settings, isLoading: settingsLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.get,
  });

  // Fetch ignore rules
  const { data: ignoreTypes = [], isLoading: typesLoading } = useQuery({
    queryKey: ['ignore-types'],
    queryFn: ignoreRulesApi.listTypes,
  });

  const { data: ignoreDomains = [], isLoading: domainsLoading } = useQuery({
    queryKey: ['ignore-domains'],
    queryFn: ignoreRulesApi.listDomains,
  });

  // State for form
  const [skipRecentDays, setSkipRecentDays] = useState<number>(settings?.skip_recent_days || 15);
  const [verifiedOnly, setVerifiedOnly] = useState<boolean>(settings?.verified_only || false);
  const [orgReposOnly, setOrgReposOnly] = useState<boolean>(settings?.org_repos_only || false);
  const [brandName, setBrandName] = useState('万联源码泄漏监控');
  const [loginTitle, setLoginTitle] = useState('登录万联源码泄漏监控');
  const [homeTitle, setHomeTitle] = useState('万联源码泄漏监控');
  const [homeDescription, setHomeDescription] = useState('持续监控公开代码平台，发现源码与敏感信息泄漏风险');

  // State for adding ignore rules
  const [newType, setNewType] = useState('');
  const [newDomain, setNewDomain] = useState('');

  // Update settings when data loads
  React.useEffect(() => {
    if (settings) {
      setSkipRecentDays(settings.skip_recent_days);
      setVerifiedOnly(settings.verified_only);
      setOrgReposOnly(settings.org_repos_only);
      setBrandName(settings.brand_name);
      setLoginTitle(settings.login_title);
      setHomeTitle(settings.home_title);
      setHomeDescription(settings.home_description);
    }
  }, [settings]);

  // Mutations
  const updateSettingsMutation = useMutation({
    mutationFn: settingsApi.update,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      queryClient.invalidateQueries({ queryKey: ['branding'] });
    },
  });

  const addTypeMutation = useMutation({
    mutationFn: ignoreRulesApi.createType,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ignore-types'] });
      setNewType('');
    },
  });

  const deleteTypeMutation = useMutation({
    mutationFn: ignoreRulesApi.deleteType,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ignore-types'] });
    },
  });

  const addDomainMutation = useMutation({
    mutationFn: ignoreRulesApi.createDomain,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ignore-domains'] });
      setNewDomain('');
    },
  });

  const deleteDomainMutation = useMutation({
    mutationFn: ignoreRulesApi.deleteDomain,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ignore-domains'] });
    },
  });

  const handleUpdateSettings = (e: React.FormEvent) => {
    e.preventDefault();
    updateSettingsMutation.mutate({
      skip_recent_days: skipRecentDays,
      verified_only: verifiedOnly,
      org_repos_only: orgReposOnly,
      brand_name: brandName,
      login_title: loginTitle,
      home_title: homeTitle,
      home_description: homeDescription,
    });
  };

  const handleAddType = (e: React.FormEvent) => {
    e.preventDefault();
    if (newType.trim()) {
      addTypeMutation.mutate({ type: newType.trim() });
    }
  };

  const handleAddDomain = (e: React.FormEvent) => {
    e.preventDefault();
    if (newDomain.trim()) {
      addDomainMutation.mutate({ domain: newDomain.trim() });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex gap-1 border-b">
        <button onClick={() => setSearchParams({ tab: 'system' })} className={`px-5 py-3 text-sm font-medium ${tab === 'system' ? 'border-b-2 border-primary text-primary' : 'text-muted-foreground'}`}>System and Ignore Rules</button>
        <button onClick={() => setSearchParams({ tab: 'exclusions' })} className={`px-5 py-3 text-sm font-medium ${tab === 'exclusions' ? 'border-b-2 border-primary text-primary' : 'text-muted-foreground'}`}>Excluded Repositories</button>
      </div>

      {tab === 'exclusions' ? <ExcludedRepositories embedded /> : <div className="space-y-6">
        {/* System Settings */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">System Settings</h2>

          {settingsLoading ? (
            <div className="text-muted-foreground">Loading...</div>
          ) : (
            <form onSubmit={handleUpdateSettings} className="space-y-4">
              <div className="rounded-lg border bg-muted/20 p-4">
                <h3 className="mb-3 font-semibold">Branding</h3>
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="text-sm"><span className="mb-1 block font-medium">Brand Name</span><input required maxLength={120} value={brandName} onChange={e => setBrandName(e.target.value)} className="w-full rounded-md border bg-background px-3 py-2" /></label>
                  <label className="text-sm"><span className="mb-1 block font-medium">Login Page Title</span><input required maxLength={160} value={loginTitle} onChange={e => setLoginTitle(e.target.value)} className="w-full rounded-md border bg-background px-3 py-2" /></label>
                  <label className="text-sm"><span className="mb-1 block font-medium">Home Page Title</span><input required maxLength={160} value={homeTitle} onChange={e => setHomeTitle(e.target.value)} className="w-full rounded-md border bg-background px-3 py-2" /></label>
                  <label className="text-sm"><span className="mb-1 block font-medium">Home Page Description</span><input required maxLength={500} value={homeDescription} onChange={e => setHomeDescription(e.target.value)} className="w-full rounded-md border bg-background px-3 py-2" /></label>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Skip Recent Days
                </label>
                <input
                  type="number"
                  min="0"
                  value={skipRecentDays}
                  onChange={(e) => setSkipRecentDays(Number(e.target.value))}
                  className="w-full max-w-xs px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Skip repositories scanned within this many days (default: 15)
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="verified-only"
                  checked={verifiedOnly}
                  onChange={(e) => setVerifiedOnly(e.target.checked)}
                  className="w-4 h-4 rounded border-input"
                />
                <label htmlFor="verified-only" className="text-sm font-medium text-foreground">
                  Verified Secrets Only
                </label>
              </div>
              <p className="text-xs text-muted-foreground">
                Only scan for verified secrets (faster, fewer false positives)
              </p>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="org-repos-only"
                  checked={orgReposOnly}
                  onChange={(e) => setOrgReposOnly(e.target.checked)}
                  className="w-4 h-4 rounded border-input"
                />
                <label htmlFor="org-repos-only" className="text-sm font-medium text-foreground">
                  Organization Repositories Only
                </label>
              </div>
              <p className="text-xs text-muted-foreground">
                Only scan repositories owned by organizations (applies to search scans only)
              </p>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={updateSettingsMutation.isPending}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  {updateSettingsMutation.isPending ? 'Saving...' : 'Save Settings'}
                </button>
                {updateSettingsMutation.isSuccess && (
                  <span className="ml-3 text-sm text-green-600">Settings saved!</span>
                )}
                {updateSettingsMutation.isError && (
                  <span className="ml-3 text-sm text-destructive">Failed to save settings</span>
                )}
              </div>
            </form>
          )}
        </div>

        {/* Ignore Finding Types */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">Ignore Finding Types</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Filter out specific detector types (e.g., "Slack", "GitHub")
          </p>

          <form onSubmit={handleAddType} className="flex gap-2 mb-4">
            <input
              type="text"
              value={newType}
              onChange={(e) => setNewType(e.target.value)}
              placeholder="Enter detector type to ignore"
              className="flex-1 px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <button
              type="submit"
              disabled={addTypeMutation.isPending || !newType.trim()}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              Add
            </button>
          </form>

          {typesLoading ? (
            <div className="text-muted-foreground">Loading...</div>
          ) : ignoreTypes.length === 0 ? (
            <div className="p-4 bg-muted rounded-lg text-center">
              <p className="text-sm text-muted-foreground">No ignored types yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {ignoreTypes.map((type) => (
                <div
                  key={type.id}
                  className="flex items-center justify-between p-3 bg-muted rounded-lg"
                >
                  <span className="text-sm font-medium">{type.type}</span>
                  <button
                    onClick={() => deleteTypeMutation.mutate(type.id)}
                    disabled={deleteTypeMutation.isPending}
                    className="text-sm text-destructive hover:text-destructive/80"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Ignore Email Domains */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">Ignore Email Domains</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Filter out findings from committers with specific email domains (e.g., github.com, example.org)
          </p>

          <form onSubmit={handleAddDomain} className="flex gap-2 mb-4">
            <input
              type="text"
              value={newDomain}
              onChange={(e) => setNewDomain(e.target.value)}
              placeholder="e.g., github.com"
              className="flex-1 px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <button
              type="submit"
              disabled={addDomainMutation.isPending || !newDomain.trim()}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              Add
            </button>
          </form>

          {domainsLoading ? (
            <div className="text-muted-foreground">Loading...</div>
          ) : ignoreDomains.length === 0 ? (
            <div className="p-4 bg-muted rounded-lg text-center">
              <p className="text-sm text-muted-foreground">No ignored domains yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {ignoreDomains.map((domain) => (
                <div
                  key={domain.id}
                  className="flex items-center justify-between p-3 bg-muted rounded-lg"
                >
                  <span className="text-sm font-medium">{domain.domain}</span>
                  <button
                    onClick={() => deleteDomainMutation.mutate(domain.id)}
                    disabled={deleteDomainMutation.isPending}
                    className="text-sm text-destructive hover:text-destructive/80"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>}
    </div>
  );
};
