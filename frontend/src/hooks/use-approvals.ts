/**
 * frontend/src/hooks/use-approvals.ts
 *
 * WHY IT EXISTS:
 * Encapsulates all React Query logic for the HITL approval system.
 * Components stay clean; all caching, polling, and mutation logic lives here.
 *
 * WHAT IT DOES:
 * - usePendingApprovals: Live-polls the pending queue every 3 seconds
 * - useApproval: Fetches a single approval's full detail
 * - useApproveWorkflow: Mutation for POST /approvals/{id}/approve
 * - useEditWorkflow: Mutation for POST /approvals/{id}/edit
 * - useRejectWorkflow: Mutation for POST /approvals/{id}/reject
 *
 * HOW IT CONNECTS TO BACKEND:
 * Calls GET/POST /api/v1/approvals/* endpoints.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export type ApprovalStatus =
  | "pending_approval"
  | "approved"
  | "edited"
  | "rejected"
  | "expired";

export interface Approval {
  id: string;
  task_id: string;
  status: ApprovalStatus;
  ai_generated_draft: string | null;
  original_input: string | null;
  workflow_context: Record<string, any> | null;
  checkpoint_node: string | null;
  human_edited_content: string | null;
  rejection_reason: string | null;
  reviewer_id: string | null;
  reviewer_name: string | null;
  decided_at: string | null;
  expires_at: string | null;
  resumed_at: string | null;
  resume_task_id: string | null;
  created_at: string;
  updated_at: string;
}

/** Poll pending approvals every 3 seconds for near-real-time queue updates */
export function usePendingApprovals(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["approvals", "pending", page, pageSize],
    queryFn: async () => {
      return apiClient.get<{ data: Approval[]; total: number }>(
        `/approvals/pending`,
        { params: { page, page_size: pageSize } }
      );
    },
    refetchInterval: 3000,
  });
}

export function useAllApprovals(page = 1, pageSize = 20, status?: ApprovalStatus) {
  return useQuery({
    queryKey: ["approvals", "all", page, pageSize, status],
    queryFn: async () => {
      return apiClient.get<{ data: Approval[]; total: number }>(
        `/approvals`,
        { params: { page, page_size: pageSize, ...(status && { status }) } }
      );
    },
    refetchInterval: 5000,
  });
}

export function useApproval(id: string) {
  return useQuery({
    queryKey: ["approval", id],
    queryFn: async () => {
      return apiClient.get<Approval>(`/approvals/${id}`);
    },
    enabled: !!id,
  });
}

/** POST /approvals/{id}/approve */
export function useApproveWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      reviewer_name,
    }: {
      id: string;
      reviewer_name?: string;
    }) => {
      return apiClient.post(`/approvals/${id}/approve`, {
        reviewer_name: reviewer_name || "Dashboard User",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
    },
  });
}

/** POST /approvals/{id}/edit */
export function useEditWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      edited_content,
      reviewer_name,
    }: {
      id: string;
      edited_content: string;
      reviewer_name?: string;
    }) => {
      return apiClient.post(`/approvals/${id}/edit`, {
        edited_content,
        reviewer_name: reviewer_name || "Dashboard User",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
    },
  });
}

/** POST /approvals/{id}/reject */
export function useRejectWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      rejection_reason,
      reviewer_name,
    }: {
      id: string;
      rejection_reason: string;
      reviewer_name?: string;
    }) => {
      return apiClient.post(`/approvals/${id}/reject`, {
        rejection_reason,
        reviewer_name: reviewer_name || "Dashboard User",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
    },
  });
}
