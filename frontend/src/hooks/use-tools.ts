/**
 * frontend/src/hooks/use-tools.ts
 *
 * WHY IT EXISTS:
 * Encapsulates the React Query logic for fetching tool execution logs.
 *
 * WHAT IT DOES:
 * Provides `useToolLogs` to retrieve the audit trail of autonomous actions.
 *
 * HOW IT CONNECTS TO BACKEND:
 * Calls `GET /api/v1/tools/logs`.
 */

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface ToolLog {
  id: string;
  tool_name: string;
  task_id: string;
  arguments: any;
  result: any;
  is_error: boolean;
  duration_ms: number;
  created_at: string;
}

export function useToolLogs(page = 1, pageSize = 50) {
  return useQuery({
    queryKey: ["tool_logs", page, pageSize],
    queryFn: async () => {
      const response = await apiClient.get<{ data: ToolLog[]; total: number }>(`/tools/logs`, {
        params: { skip: (page - 1) * pageSize, limit: pageSize }
      });
      return response;
    },
    refetchInterval: 10000, // Poll every 10s
  });
}
