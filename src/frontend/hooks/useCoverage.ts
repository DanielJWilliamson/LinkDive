import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import type { CampaignCoverageSummary, AggregateCoverageSummary } from '../types/api';

const API_PREFIX = '/api/v1';

const coverageApi = {
  getCampaignCoverage: async (id: number): Promise<CampaignCoverageSummary> => {
  const res = await apiClient.get(`${API_PREFIX}/campaigns/${id}/coverage`);
    return res.data;
  },
  getAggregateCoverage: async (): Promise<AggregateCoverageSummary> => {
  const res = await apiClient.get(`${API_PREFIX}/coverage/summary`);
    return res.data;
  }
};

export function useCampaignCoverage(id: number | null) {
  return useQuery({
    queryKey: ['campaign-coverage', id],
    queryFn: () => coverageApi.getCampaignCoverage(id!),
    enabled: !!id,
    staleTime: 60 * 1000
  });
}

export function useAggregateCoverage() {
  return useQuery({
    queryKey: ['aggregate-coverage'],
    queryFn: coverageApi.getAggregateCoverage,
    staleTime: 60 * 1000
  });
}
