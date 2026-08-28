import { useQuery } from '@tanstack/react-query';
import { brandingApi } from '@/services/api';

const defaults = {
  brand_name: '万联源码泄漏监控',
  login_title: '登录万联源码泄漏监控',
  home_title: '万联源码泄漏监控',
  home_description: '持续监控公开代码平台，发现源码与敏感信息泄漏风险',
};

export function useBranding() {
  const query = useQuery({ queryKey: ['branding'], queryFn: brandingApi.get, staleTime: 60_000 });
  return query.data ?? defaults;
}
