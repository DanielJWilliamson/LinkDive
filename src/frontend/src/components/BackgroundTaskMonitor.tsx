import React, { useState } from 'react';
import { 
  useUserTasks, 
  useTaskStatus, 
  useTaskResult, 
  useCancelTask,
  getTaskStatusColor,
  formatTaskType 
} from '../hooks/useBackgroundTasks';

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

interface BackgroundTaskMonitorProps {
  userEmail: string;
  campaignId?: number;
  className?: string;
}

// Utility functions
const formatDuration = (minutes?: number): string => {
  if (!minutes) return 'Unknown';
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m`;
};

const formatTimeAgo = (dateStr: string): string => {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
};

const BackgroundTaskMonitor: React.FC<BackgroundTaskMonitorProps> = ({
  userEmail,
  campaignId,
  className = ""
}) => {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data: tasks = [], isLoading: tasksLoading } = useUserTasks(userEmail, statusFilter || undefined);
  const { data: taskResult } = useTaskResult(selectedTaskId || '', userEmail, !!selectedTaskId);
  const cancelTaskMutation = useCancelTask();

  // Filter tasks by campaign if specified
  const filteredTasks = campaignId 
    ? tasks.filter(task => task.campaign_id === campaignId)
    : tasks;

  const handleCancelTask = async (taskId: string) => {
    try {
      await cancelTaskMutation.mutateAsync({ taskId, userEmail });
    } catch (error) {
      console.error('Failed to cancel task:', error);
    }
  };

  if (tasksLoading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Background Tasks
            {campaignId && <span className="text-sm text-gray-500 ml-2">Campaign {campaignId}</span>}
          </h3>
          
          {/* Status filter */}
          <div className="flex items-center space-x-2">
            <label htmlFor="status-filter" className="text-sm text-gray-600">
              Status:
            </label>
            <select
              id="status-filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="">All</option>
              <option value="pending">Pending</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>
      </div>

      <div className="p-6">
        {filteredTasks.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p>No background tasks found</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                userEmail={userEmail}
                onCancel={handleCancelTask}
                onViewResult={() => setSelectedTaskId(task.id)}
                isSelected={selectedTaskId === task.id}
              />
            ))}
          </div>
        )}

        {/* Task Result Modal */}
        {selectedTaskId && taskResult && (
          <TaskResultModal
            result={taskResult}
            onClose={() => setSelectedTaskId(null)}
          />
        )}
      </div>
    </div>
  );
};

interface TaskCardProps {
  task: BackgroundTask;
  userEmail: string;
  onCancel: (taskId: string) => void;
  onViewResult: () => void;
  isSelected: boolean;
}

const TaskCard: React.FC<TaskCardProps> = ({ 
  task, 
  userEmail, 
  onCancel, 
  onViewResult, 
  isSelected 
}) => {
  const { data: liveTask } = useTaskStatus(task.id, userEmail);
  const currentTask = liveTask || task;

  const canCancel = ['pending', 'running'].includes(currentTask.status);
  const hasResult = currentTask.status === 'completed';

  return (
    <div className={`border rounded-lg p-4 ${isSelected ? 'ring-2 ring-blue-500' : ''}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${
            currentTask.status === 'completed' ? 'bg-green-500' :
            currentTask.status === 'failed' ? 'bg-red-500' :
            currentTask.status === 'running' ? 'bg-blue-500 animate-pulse' :
            currentTask.status === 'pending' ? 'bg-yellow-500' :
            'bg-gray-500'
          }`}></div>
          
          <div>
            <h4 className="font-medium text-gray-900">
              {formatTaskType(currentTask.task_type)}
            </h4>
            <p className="text-sm text-gray-500">
              ID: {currentTask.id.split('-').pop()}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className={`text-sm font-medium ${getTaskStatusColor(currentTask.status)}`}>
            {currentTask.status.toUpperCase()}
          </span>
          
          {hasResult && (
            <button
              onClick={onViewResult}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              View Result
            </button>
          )}
          
          {canCancel && (
            <button
              onClick={() => onCancel(currentTask.id)}
              className="text-red-600 hover:text-red-800 text-sm font-medium"
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* Progress bar for running tasks */}
      {currentTask.status === 'running' && (
        <div className="mb-3">
          <div className="flex justify-between text-xs text-gray-600 mb-1">
            <span>Progress</span>
            <span>{Math.round(currentTask.progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${currentTask.progress}%` }}
            ></div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between text-sm text-gray-600">
        <div className="flex items-center space-x-4">
          <span>Created {formatTimeAgo(currentTask.created_at)}</span>
          {currentTask.estimated_duration_minutes && (
            <span>Est. {formatDuration(currentTask.estimated_duration_minutes)}</span>
          )}
        </div>

        {currentTask.error_message && (
          <span className="text-red-600 text-xs truncate max-w-xs">
            Error: {currentTask.error_message}
          </span>
        )}
      </div>
    </div>
  );
};

interface TaskResultModalProps {
  result: Record<string, unknown>;
  onClose: () => void;
}

const TaskResultModal: React.FC<TaskResultModalProps> = ({ 
  result, 
  onClose 
}) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-4xl max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b">
          <h3 className="text-lg font-semibold">Task Result</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default BackgroundTaskMonitor;
