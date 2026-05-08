/**
 * frontend/src/hooks/use-tasks.ts
 *
 * WHY IT EXISTS:
 * Encapsulates the React Query logic for fetching workflow tasks. This keeps components
 * clean and ensures caching, refetching, and error handling are centralized.
 *
 * WHAT IT DOES:
 * Provides `useTasks` for pagination and `useTask` for detailed inspection.
 *
 * HOW IT CONNECTS TO BACKEND:
 * Calls `GET /api/v1/tasks/` and `GET /api/v1/tasks/{id}`.
 */

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface Task {
  id: string;
  source: string;
  payload: any;
  status: "QUEUED" | "PROCESSING" | "COMPLETED" | "FAILED" | "RETRYING";
  result_data?: any;
  error_message?: string;
  retry_count: number;
  created_at: string;
  updated_at: string;
}

export function useTasks(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["tasks", page, pageSize],
    queryFn: async () => {
      const response = await apiClient.get<{ data: Task[]; total: number }>(`/tasks/`, {
        params: { page, page_size: pageSize }
      });
      // Handle nested envelope if necessary
      return response.data || response;
    },
    refetchInterval: 5000, // Poll every 5s for real-time updates
  });
}

export function useTask(id: string) {
  return useQuery({
    queryKey: ["task", id],
    queryFn: async () => {
      const response = await apiClient.get<Task>(`/tasks/${id}`);
      return response;
    },
    enabled: !!id,
  });
}
