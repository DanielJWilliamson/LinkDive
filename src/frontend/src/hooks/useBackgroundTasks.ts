import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, DEV_USER_EMAIL } from '../../lib/api';

interface BackgroundTask {
  id: string;
  task_type: string;
  status: string;
  campaign_id?: number;
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  estimated_duration_minutes?: number;
  error_message?: string;
}

interface TaskRequest {
  task_type: string;
  campaign_id?: number;
  parameters?: Record<string, unknown>;
}

interface CreateTaskResponse {
  task_id: string;
  message: string;
  estimated_duration_minutes: number;
}

// Base API prefix for background routes
const API_PREFIX = '/api/background';

// Fetch task status
const fetchTaskStatus = async (taskId: string, userEmail: string): Promise<BackgroundTask> => {
  const { data } = await apiClient.get(`${API_PREFIX}/tasks/${taskId}`, {
    params: { user_email: userEmail },
  });
  return data;
};

// Fetch task result
const fetchTaskResult = async (taskId: string, userEmail: string) => {
  const { data } = await apiClient.get(`${API_PREFIX}/tasks/${taskId}/result`, {
    params: { user_email: userEmail },
  });
  return data;
};

// Fetch all tasks for user
const fetchUserTasks = async (userEmail: string, status?: string): Promise<BackgroundTask[]> => {
  const { data } = await apiClient.get(`${API_PREFIX}/tasks`, {
    params: { user_email: userEmail, status },
  });
  return data;
};

// Create background task
const createBackgroundTask = async (
  userEmail: string, 
  taskRequest: TaskRequest
): Promise<CreateTaskResponse> => {
  const { data } = await apiClient.post(`${API_PREFIX}/tasks`, taskRequest, {
    params: { user_email: userEmail },
  });
  return data;
};

// Start campaign analysis
const startCampaignAnalysis = async (
  campaignId: number,
  userEmail: string,
  analysisDepth = 'standard',
  includeContentVerification = false
): Promise<CreateTaskResponse> => {
  const params = new URLSearchParams({
    user_email: userEmail,
    analysis_depth: analysisDepth,
    include_content_verification: includeContentVerification.toString(),
  });
  
  const { data } = await apiClient.post(`${API_PREFIX}/campaigns/${campaignId}/analyze`, null, {
    params: Object.fromEntries(params),
  });
  return data;
};

// Cancel task
const cancelTask = async (taskId: string, userEmail: string): Promise<void> => {
  await apiClient.delete(`${API_PREFIX}/tasks/${taskId}`, {
    params: { user_email: userEmail },
  });
};

// React Query hooks
export const useTaskStatus = (taskId: string, userEmail: string, enabled = true) => {
  return useQuery({
    queryKey: ['taskStatus', taskId, userEmail],
    queryFn: () => fetchTaskStatus(taskId, userEmail || DEV_USER_EMAIL),
    enabled: enabled && !!taskId && !!(userEmail || DEV_USER_EMAIL),
    refetchInterval: (query) => {
      // Poll more frequently for running tasks
      const data = query.state.data;
      if (data?.status === 'running') return 2000; // 2 seconds
      if (data?.status === 'pending') return 5000; // 5 seconds
      return false; // Don't poll completed/failed tasks
    },
  });
};

export const useTaskResult = (taskId: string, userEmail: string, enabled = true) => {
  return useQuery({
    queryKey: ['taskResult', taskId, userEmail],
    queryFn: () => fetchTaskResult(taskId, userEmail || DEV_USER_EMAIL),
    enabled: enabled && !!taskId && !!(userEmail || DEV_USER_EMAIL),
  });
};

export const useUserTasks = (userEmail: string, status?: string) => {
  return useQuery({
    queryKey: ['userTasks', userEmail, status],
    queryFn: () => fetchUserTasks(userEmail || DEV_USER_EMAIL, status),
    enabled: !!(userEmail || DEV_USER_EMAIL),
    refetchInterval: 10000, // Refresh every 10 seconds
  });
};

export const useCreateBackgroundTask = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ userEmail, taskRequest }: { 
      userEmail: string; 
      taskRequest: TaskRequest 
    }) => createBackgroundTask(userEmail, taskRequest),
    onSuccess: (_, { userEmail }) => {
      // Invalidate user tasks to show the new task
      queryClient.invalidateQueries({ queryKey: ['userTasks', userEmail] });
    },
  });
};

export const useStartCampaignAnalysis = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ 
      campaignId, 
      userEmail, 
      analysisDepth, 
      includeContentVerification 
    }: {
      campaignId: number;
      userEmail: string;
      analysisDepth?: string;
      includeContentVerification?: boolean;
    }) => startCampaignAnalysis(
      campaignId, 
      userEmail, 
      analysisDepth, 
      includeContentVerification
    ),
    onSuccess: (_, { userEmail }) => {
      queryClient.invalidateQueries({ queryKey: ['userTasks', userEmail] });
    },
  });
};

export const useCancelTask = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ taskId, userEmail }: { taskId: string; userEmail: string }) =>
      cancelTask(taskId, userEmail),
    onSuccess: (_, { userEmail, taskId }) => {
      // Invalidate task status and user tasks
      queryClient.invalidateQueries({ queryKey: ['taskStatus', taskId] });
      queryClient.invalidateQueries({ queryKey: ['userTasks', userEmail] });
    },
  });
};

// Helper function to get status color
export const getTaskStatusColor = (status: string): string => {
  switch (status) {
    case 'completed':
      return 'text-green-600';
    case 'failed':
      return 'text-red-600';
    case 'running':
      return 'text-blue-600';
    case 'pending':
      return 'text-yellow-600';
    case 'cancelled':
      return 'text-gray-600';
    default:
      return 'text-gray-500';
  }
};

// Helper function to format task type
export const formatTaskType = (taskType: string): string => {
  switch (taskType) {
    case 'campaign_analysis':
      return 'Campaign Analysis';
    case 'content_verification':
      return 'Content Verification';
    case 'scheduled_monitoring':
      return 'Scheduled Monitoring';
    case 'batch_update':
      return 'Batch Update';
    default:
      return taskType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
};
