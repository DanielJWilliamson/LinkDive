import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';

const API_PREFIX = '/api/v1/runtime';

export interface RuntimeConfig {
  mock_mode: boolean;
  provider_errors: Record<string, string>;
}

export function useRuntimeConfig() {
  return useQuery<RuntimeConfig>({
    queryKey: ['runtime-config'],
    queryFn: async () => {
      const res = await apiClient.get(`${API_PREFIX}/config`);
      return res.data as RuntimeConfig;
    },
    staleTime: 30 * 1000,
  });
}

export function useSetMockMode() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (mock_mode: boolean) => {
      const res = await apiClient.post(`${API_PREFIX}/config`, { mock_mode });
      return res.data as RuntimeConfig;
    },
    onSuccess: (data) => {
      qc.setQueryData(['runtime-config'], data);
    },
  });
}
