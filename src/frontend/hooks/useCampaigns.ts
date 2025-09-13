import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';

// API base path (apiClient baseURL points at host root)
const API_PREFIX = '/api/v1';

// Types
interface Campaign {
  id: number;
  user_email: string;
  client_name: string;
  campaign_name: string;
  client_domain: string;
  campaign_url?: string;
  launch_date?: string;
  monitoring_status: string;
  created_at: string;
  updated_at: string;
  auto_pause_date?: string;
}

interface CampaignFormData {
  client_name: string;
  campaign_name: string;
  client_domain: string;
  campaign_url?: string;
  launch_date?: string;
  serp_keywords: string[];
  verification_keywords: string[];
  blacklist_domains: string[];
}

interface BacklinkResult {
  id: number;
  url: string;
  page_title?: string;
  first_seen?: string;
  coverage_status: string;
  source_api: string;
  domain_rating?: number;
  confidence_score?: string;
  link_destination?: string;
}

interface CampaignResults {
  campaign: Campaign;
  results: BacklinkResult[];
  total_results: number;
  verified_coverage: number;
  potential_coverage: number;
}

// API functions
const campaignApi = {
  getCampaigns: async (): Promise<Campaign[]> => {
  const response = await apiClient.get(`${API_PREFIX}/campaigns`);
    return response.data;
  },

  getCampaign: async (id: number): Promise<Campaign> => {
  const response = await apiClient.get(`${API_PREFIX}/campaigns/${id}`);
    return response.data;
  },

  createCampaign: async (data: CampaignFormData): Promise<Campaign> => {
  const response = await apiClient.post(`${API_PREFIX}/campaigns`, data);
    return response.data;
  },

  updateCampaign: async (id: number, data: Partial<CampaignFormData>): Promise<Campaign> => {
  const response = await apiClient.put(`${API_PREFIX}/campaigns/${id}`, data);
    return response.data;
  },

  deleteCampaign: async (id: number): Promise<void> => {
  await apiClient.delete(`${API_PREFIX}/campaigns/${id}`);
  },

  analyzeCampaign: async (id: number): Promise<CampaignResults> => {
  const response = await apiClient.post(`${API_PREFIX}/campaigns/${id}/analyze`);
    return response.data;
  },

  getCampaignResults: async (id: number): Promise<CampaignResults> => {
  const response = await apiClient.get(`${API_PREFIX}/campaigns/${id}/results`);
    return response.data;
  },

  getCoverageDetails: async (
    id: number,
    params: { status?: 'all' | 'verified' | 'potential'; search?: string }
  ): Promise<BacklinkResult[]> => {
    const response = await apiClient.get(`${API_PREFIX}/campaigns/${id}/coverage/details`, {
      params: {
        status: params.status ?? 'all',
        search: params.search || undefined,
      },
    });
    return response.data;
  }
};

// React Query hooks
export function useCampaigns() {
  return useQuery({
    queryKey: ['campaigns'],
    queryFn: campaignApi.getCampaigns,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCampaign(id: number | null) {
  return useQuery({
    queryKey: ['campaign', id],
    queryFn: () => campaignApi.getCampaign(id!),
    enabled: !!id,
  });
}

export function useCreateCampaign() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: campaignApi.createCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });
}

export function useUpdateCampaign() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CampaignFormData> }) =>
      campaignApi.updateCampaign(id, data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      queryClient.invalidateQueries({ queryKey: ['campaign', variables.id] });
    },
  });
}

export function useDeleteCampaign() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: campaignApi.deleteCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });
}

export function useAnalyzeCampaign() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: campaignApi.analyzeCampaign,
    onSuccess: (data, campaignId) => {
      queryClient.setQueryData(['campaign-results', campaignId], data);
      // Refresh coverage details table as analysis may have added rows
      queryClient.invalidateQueries({
        queryKey: ['coverage-details', campaignId],
        exact: false,
      });
    },
  });
}

export function useCampaignResults(id: number | null) {
  return useQuery({
    queryKey: ['campaign-results', id],
    queryFn: () => campaignApi.getCampaignResults(id!),
    enabled: !!id,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useCoverageDetails(
  id: number | null,
  params: { status?: 'all' | 'verified' | 'potential'; search?: string } = {}
) {
  return useQuery({
    queryKey: ['coverage-details', id, params.status ?? 'all', params.search ?? ''],
    queryFn: () => campaignApi.getCoverageDetails(id!, params),
    enabled: !!id,
    staleTime: 60 * 1000, // 1 minute
  });
}

// Export types for use in components
export type {
  Campaign,
  CampaignFormData,
  BacklinkResult,
  CampaignResults
};
