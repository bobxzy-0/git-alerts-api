import apiClient from '@/lib/api-client';
import type {
  LoginCredentials,
  TokenResponse,
  Scan,
  CreateScanRequest,
  Finding,
  PaginatedResponse,
  IgnoreFindingType,
  IgnoreFindingDomain,
  CreateIgnoreTypeRequest,
  CreateIgnoreDomainRequest,
  UserIntegration,
  CreateIntegrationRequest,
  SystemSettings,
  UpdateSystemSettingsRequest,
  DashboardSummary,
  MonitorRule,
  SourceHealth,
  NotificationChannel,
  MonitoringProfile,
  ScanRepository,
  ExcludedRepository,
} from '@/types';

// Auth API
export const authApi = {
  login: async (credentials: LoginCredentials): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/api/token/', credentials);
    return response.data;
  },

  refreshToken: async (refresh: string): Promise<{ access: string }> => {
    const response = await apiClient.post<{ access: string }>('/api/token/refresh/', { refresh });
    return response.data;
  },
};

export const dashboardApi = { get: async (): Promise<DashboardSummary> => (await apiClient.get<DashboardSummary>('/dashboard/')).data };
export const sourceHealthApi = { list: async (): Promise<SourceHealth[]> => (await apiClient.get<SourceHealth[]>('/source-health/')).data };
export const monitorRulesApi = {
  list: async (): Promise<MonitorRule[]> => (await apiClient.get<MonitorRule[]>('/monitor-rules/')).data,
  create: async (data: Pick<MonitorRule, 'name' | 'enabled' | 'source' | 'scan_type' | 'value' | 'interval_minutes'> & Partial<Pick<MonitorRule, 'schedule_kind' | 'schedule_time' | 'schedule_weekdays' | 'cron_expression'>>): Promise<MonitorRule> => (await apiClient.post<MonitorRule>('/monitor-rules/', data)).data,
  update: async (id: number, data: Partial<MonitorRule>): Promise<MonitorRule> => (await apiClient.patch<MonitorRule>(`/monitor-rules/${id}/`, data)).data,
  delete: async (id: number): Promise<void> => { await apiClient.delete(`/monitor-rules/${id}/`); },
  runNow: async (id: number): Promise<Scan> => (await apiClient.post<Scan>(`/monitor-rules/${id}/run/`)).data,
};

export const notificationChannelsApi = {
  list: async (): Promise<NotificationChannel[]> => (await apiClient.get<NotificationChannel[]>('/notifications/channels/')).data,
  create: async (data: Pick<NotificationChannel,'name'|'channel_type'|'target'|'enabled'>): Promise<NotificationChannel> => (await apiClient.post<NotificationChannel>('/notifications/channels/',data)).data,
  update: async (id:number, data:Partial<NotificationChannel>): Promise<NotificationChannel> => (await apiClient.patch<NotificationChannel>(`/notifications/channels/${id}/`,data)).data,
  delete: async (id:number): Promise<void> => { await apiClient.delete(`/notifications/channels/${id}/`); },
};

export const monitoringProfilesApi = {
  list: async (): Promise<MonitoringProfile[]> => (await apiClient.get<MonitoringProfile[]>('/monitoring-profiles/')).data,
  create: async (data: Omit<MonitoringProfile, 'id' | 'generated_rule_count' | 'schedule_kind' | 'schedule_time' | 'schedule_weekdays' | 'cron_expression'> & Partial<Pick<MonitoringProfile, 'schedule_kind' | 'schedule_time' | 'schedule_weekdays' | 'cron_expression'>>): Promise<MonitoringProfile> => (await apiClient.post<MonitoringProfile>('/monitoring-profiles/', data)).data,
  delete: async (id: number): Promise<void> => { await apiClient.delete(`/monitoring-profiles/${id}/`); },
};

// Scans API
export const scansApi = {
  list: async (params?: {
    type?: string;
    value?: string;
    execution_status?: string;
    monitoring_status?: string;
    result_status?: string;
    trigger_type?: string;
    created_at?: string;
    completed_at?: string;
  }): Promise<Scan[]> => {
    const queryParams = new URLSearchParams();
    if (params?.type) queryParams.append('type', params.type);
    if (params?.value) queryParams.append('value', params.value);
    if (params?.execution_status) queryParams.append('execution_status', params.execution_status);
    if (params?.monitoring_status) queryParams.append('monitoring_status', params.monitoring_status);
    if (params?.result_status) queryParams.append('result_status', params.result_status);
    if (params?.trigger_type) queryParams.append('trigger_type', params.trigger_type);
    if (params?.created_at) queryParams.append('created_at', params.created_at);
    if (params?.completed_at) queryParams.append('completed_at', params.completed_at);

    const response = await apiClient.get<Scan[]>(
      `/scans/?${queryParams.toString()}`
    );
    return response.data;
  },

  get: async (id: number): Promise<Scan> => {
    const response = await apiClient.get<Scan>(`/scans/${id}/`);
    return response.data;
  },

  create: async (data: CreateScanRequest): Promise<Scan> => {
    const response = await apiClient.post<Scan>('/scans/', data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/scans/${id}/`);
  },

  getFindings: async (scanId: number, page = 1): Promise<PaginatedResponse<Finding>> => {
    const response = await apiClient.get<PaginatedResponse<Finding>>(
      `/scans/${scanId}/findings/?page=${page}`
    );
    return response.data;
  },
  getRepositories: async (scanId: number): Promise<ScanRepository[]> => (await apiClient.get<ScanRepository[]>(`/scans/${scanId}/repositories/`)).data,
};

export const excludedRepositoriesApi = {
  list: async (): Promise<ExcludedRepository[]> => (await apiClient.get<ExcludedRepository[]>('/excluded-repositories/')).data,
  create: async (data: Pick<ExcludedRepository, 'source' | 'repository_url' | 'owner' | 'repository' | 'reason' | 'enabled'>): Promise<ExcludedRepository> => (await apiClient.post<ExcludedRepository>('/excluded-repositories/', data)).data,
  update: async (id: number, data: Partial<ExcludedRepository>): Promise<ExcludedRepository> => (await apiClient.patch<ExcludedRepository>(`/excluded-repositories/${id}/`, data)).data,
  delete: async (id: number): Promise<void> => { await apiClient.delete(`/excluded-repositories/${id}/`); },
};

// Findings API
export const findingsApi = {
  list: async (params?: {
    type?: string;
    value?: string;
    email?: string;
    repository?: string;
    scan?: number;
    validated?: boolean;
    created_at?: string;
  }): Promise<Finding[]> => {
    const queryParams = new URLSearchParams();
    if (params?.type) queryParams.append('type', params.type);
    if (params?.value) queryParams.append('value', params.value);
    if (params?.email) queryParams.append('email', params.email);
    if (params?.repository) queryParams.append('repository', params.repository);
    if (params?.scan) queryParams.append('scan', params.scan.toString());
    if (params?.validated !== undefined) queryParams.append('validated', params.validated.toString());
    if (params?.created_at) queryParams.append('created_at', params.created_at);

    const response = await apiClient.get<Finding[]>(
      `/findings/?${queryParams.toString()}`
    );
    return response.data;
  },

  get: async (id: number): Promise<Finding> => {
    const response = await apiClient.get<Finding>(`/findings/${id}/`);
    return response.data;
  },

  update: async (id: number, data: Partial<Finding>): Promise<Finding> => {
    const response = await apiClient.patch<Finding>(`/findings/${id}/`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/findings/${id}/`);
  },
};

// Ignore Rules API
export const ignoreRulesApi = {
  // Finding Types
  listTypes: async (): Promise<IgnoreFindingType[]> => {
    const response = await apiClient.get<IgnoreFindingType[]>('/finding-ignores/types/');
    return response.data;
  },

  createType: async (data: CreateIgnoreTypeRequest): Promise<IgnoreFindingType> => {
    const response = await apiClient.post<IgnoreFindingType>('/finding-ignores/types/', data);
    return response.data;
  },

  deleteType: async (id: number): Promise<void> => {
    await apiClient.delete(`/finding-ignores/types/${id}`);
  },

  // Finding Domains
  listDomains: async (): Promise<IgnoreFindingDomain[]> => {
    const response = await apiClient.get<IgnoreFindingDomain[]>('/finding-ignores/domains/');
    return response.data;
  },

  createDomain: async (data: CreateIgnoreDomainRequest): Promise<IgnoreFindingDomain> => {
    const response = await apiClient.post<IgnoreFindingDomain>('/finding-ignores/domains/', data);
    return response.data;
  },

  deleteDomain: async (id: number): Promise<void> => {
    await apiClient.delete(`/finding-ignores/domains/${id}`);
  },
};

// Integrations API
export const integrationsApi = {
  list: async (): Promise<UserIntegration[]> => {
    const response = await apiClient.get<UserIntegration[]>('/integrations/');
    return response.data;
  },

  create: async (data: CreateIntegrationRequest): Promise<UserIntegration> => {
    const response = await apiClient.post<UserIntegration>('/integrations/', data);
    return response.data;
  },

  validate: async (id: number): Promise<{ message: string; integration_id: number; provider: string; status: string }> => {
    const response = await apiClient.post(`/integrations/${id}/validate/`);
    return response.data;
  },
};

// Settings API
export const settingsApi = {
  get: async (): Promise<SystemSettings> => {
    const response = await apiClient.get<SystemSettings>('/settings/');
    return response.data;
  },

  update: async (data: UpdateSystemSettingsRequest): Promise<SystemSettings> => {
    const response = await apiClient.patch<SystemSettings>('/settings/', data);
    return response.data;
  },
};
