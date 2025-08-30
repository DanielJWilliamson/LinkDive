/**
 * React Query hooks for Link Dive AI API calls
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api';
import type {
  DomainMetrics,
  BacklinkResponse,
  HealthStatus,
  DetailedHealthStatus,
  CompetitorAnalysisResponse,
  RiskAssessment,
} from '@/types/api';

// Query keys for React Query
export const queryKeys = {
  health: ['health'] as const,
  healthDetailed: ['health', 'detailed'] as const,
  domainMetrics: (domain: string) => ['domain', domain, 'metrics'] as const,
  backlinks: (target: string, params?: Record<string, unknown>) => ['backlinks', target, params] as const,
  competitorAnalysis: (target: string, competitors: string[]) => 
    ['competitor-analysis', target, competitors] as const,
  riskAssessment: (domain: string) => ['risk-assessment', domain] as const,
};

// Health check hooks
export function useHealthCheck() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: async (): Promise<HealthStatus> => {
      const response = await apiClient.get('/api/v1/health/');
      return response.data;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

export function useDetailedHealthCheck() {
  return useQuery({
    queryKey: queryKeys.healthDetailed,
    queryFn: async (): Promise<DetailedHealthStatus> => {
      const response = await apiClient.get('/api/v1/health/detailed');
      return response.data;
    },
    refetchInterval: 60000, // Refetch every minute
  });
}

// Domain metrics hook
export function useDomainMetrics(domain: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.domainMetrics(domain),
    queryFn: async (): Promise<DomainMetrics> => {
      const response = await apiClient.get(`/api/v1/backlinks/domain/${domain}/metrics`);
      return response.data;
    },
    enabled: enabled && !!domain,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Backlink analysis hook
export function useBacklinkAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: {
      target_url: string;
      mode?: string;
      limit?: number;
      offset?: number;
      include_subdomains?: boolean;
    }): Promise<BacklinkResponse> => {
      const response = await apiClient.post('/api/v1/backlinks/analyze', params);
      return response.data;
    },
    onSuccess: (data, variables) => {
      // Cache the result
      queryClient.setQueryData(
        queryKeys.backlinks(variables.target_url, variables),
        data
      );
    },
  });
}

// Competitor analysis hook
export function useCompetitorAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: {
      target_domain: string;
      competitor_domains: string[];
      analysis_depth?: string;
    }): Promise<CompetitorAnalysisResponse> => {
      const response = await apiClient.post('/api/v1/backlinks/competitor-analysis', null, {
        params,
      });
      return response.data;
    },
    onSuccess: (data, variables) => {
      // Cache the result
      queryClient.setQueryData(
        queryKeys.competitorAnalysis(variables.target_domain, variables.competitor_domains),
        data
      );
    },
  });
}

// Risk assessment hook
export function useRiskAssessment(domain: string, severity: string = 'all', enabled = true) {
  return useQuery({
    queryKey: queryKeys.riskAssessment(domain),
    queryFn: async (): Promise<RiskAssessment> => {
      const response = await apiClient.get(`/api/v1/backlinks/${domain}/risks`, {
        params: { severity },
      });
      return response.data;
    },
    enabled: enabled && !!domain,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

// Custom hook for getting cached backlink data
export function useBacklinkData(target: string, params?: Record<string, unknown>) {
  return useQuery({
    queryKey: queryKeys.backlinks(target, params),
    queryFn: () => {
      // This will only return cached data, not make a new request
      throw new Error('This should only be used to access cached data');
    },
    enabled: false,
  });
}
