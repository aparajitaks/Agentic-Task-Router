"use client";

/**
 * frontend/src/app/(dashboard)/approvals/page.tsx
 *
 * WHY IT EXISTS:
 * This is the human operator's control room for reviewing AI-generated content
 * before it reaches the real world (external email recipients). It is the most
 * critical page in an enterprise HITL system — the place where humans govern AI.
 *
 * WHAT IT DOES:
 * - Displays the pending approval queue with live 3-second polling
 * - Shows original email input + AI-generated draft side by side
 * - Provides inline text editing for corrections before approval
 * - Tracks full approval history in a filterable audit log tab
 * - Animates live status updates as decisions are made
 *
 * HOW IT CONNECTS TO BACKEND:
 * Uses `use-approvals.ts` hooks → GET/POST /api/v1/approvals/*
 */

import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import {
  Check,
  X,
  Edit3,
  Clock,
  AlertTriangle,
  Bot,
  User,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";

import type { Approval } from "@/hooks/use-approvals";
import {
  usePendingApprovals,
  useAllApprovals,
  useApproveWorkflow,
  useEditWorkflow,
  useRejectWorkflow,
} from "@/hooks/use-approvals";

// ── Status Badge ──────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: Approval["status"] }) {
  const config: Record<string, { label: string; className: string }> = {
    pending_approval: { label: "Pending Review", className: "bg-amber-500/15 text-amber-400 border-amber-500/30" },
    approved: { label: "Approved", className: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" },
    edited: { label: "Edited & Approved", className: "bg-blue-500/15 text-blue-400 border-blue-500/30" },
    rejected: { label: "Rejected", className: "bg-red-500/15 text-red-400 border-red-500/30" },
    expired: { label: "Expired", className: "bg-gray-500/15 text-gray-400 border-gray-500/30" },
  };
  const { label, className } = config[status] ?? config.pending_approval;
  return (
    <Badge variant="outline" className={className}>
      {label}
    </Badge>
  );
}

// ── Approval Review Card ──────────────────────────────────────────────────────

function ApprovalCard({ approval }: { approval: Approval }) {
  const [expanded, setExpanded] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(approval.ai_generated_draft || "");
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectForm, setShowRejectForm] = useState(false);

  const approveMutation = useApproveWorkflow();
  const editMutation = useEditWorkflow();
  const rejectMutation = useRejectWorkflow();

  const isPending = approval.status === "pending_approval";
  const isLoading =
    approveMutation.isPending || editMutation.isPending || rejectMutation.isPending;

  const handleApprove = () => {
    approveMutation.mutate({ id: approval.id });
  };

  const handleEdit = () => {
    editMutation.mutate({ id: approval.id, edited_content: editedContent });
    setIsEditing(false);
  };

  const handleReject = () => {
    if (!rejectReason.trim() || rejectReason.length < 10) return;
    rejectMutation.mutate({ id: approval.id, rejection_reason: rejectReason });
    setShowRejectForm(false);
  };

  return (
    <Card className="border-muted/60 transition-all duration-300 hover:border-muted">
      {/* Card Header */}
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <StatusBadge status={approval.status} />
              <Badge variant="secondary" className="font-mono text-xs">
                {approval.workflow_context?.selected_agent || "reply_generator_agent"}
              </Badge>
              <Badge variant="outline" className="font-mono text-[10px] text-muted-foreground">
                {approval.id.slice(0, 8)}
              </Badge>
            </div>
            <CardDescription>
              Created {formatDistanceToNow(new Date(approval.created_at), { addSuffix: true })}
              {approval.expires_at && approval.status === "pending_approval" && (
                <span className="ml-2 text-amber-400">
                  · Expires {formatDistanceToNow(new Date(approval.expires_at), { addSuffix: true })}
                </span>
              )}
            </CardDescription>
          </div>

          <div className="flex items-center gap-2">
            {isPending && (
              <>
                {!isEditing && !showRejectForm && (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10"
                      onClick={handleApprove}
                      disabled={isLoading}
                    >
                      <Check className="h-3.5 w-3.5 mr-1.5" />
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-blue-400 border-blue-500/30 hover:bg-blue-500/10"
                      onClick={() => setIsEditing(true)}
                      disabled={isLoading}
                    >
                      <Edit3 className="h-3.5 w-3.5 mr-1.5" />
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-400 border-red-500/30 hover:bg-red-500/10"
                      onClick={() => setShowRejectForm(true)}
                      disabled={isLoading}
                    >
                      <X className="h-3.5 w-3.5 mr-1.5" />
                      Reject
                    </Button>
                  </>
                )}
              </>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </CardHeader>

      {/* Expandable Detail Panel */}
      {expanded && (
        <CardContent className="pt-0 space-y-4">
          <Separator />

          {/* Two-column layout: original input vs AI draft */}
          <div className="grid md:grid-cols-2 gap-4">
            {/* Original Email Input */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                <User className="h-3.5 w-3.5" />
                Original Input
              </div>
              <ScrollArea className="h-40 rounded-md border border-muted/60 bg-muted/20 p-3">
                <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
                  {approval.original_input || "No original input recorded."}
                </p>
              </ScrollArea>
            </div>

            {/* AI-Generated Draft */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                <Bot className="h-3.5 w-3.5 text-primary" />
                AI-Generated Draft
              </div>
              {isEditing ? (
                <div className="space-y-2">
                  <Textarea
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    className="h-40 resize-none text-sm bg-muted/20 border-primary/50 focus-visible:ring-primary/30"
                    placeholder="Edit the AI response..."
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={handleEdit}
                      disabled={isLoading || !editedContent.trim()}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <Check className="h-3.5 w-3.5 mr-1.5" />
                      Approve Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setIsEditing(false);
                        setEditedContent(approval.ai_generated_draft || "");
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <ScrollArea className="h-40 rounded-md border border-primary/20 bg-primary/5 p-3">
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">
                    {approval.ai_generated_draft || "No draft generated."}
                  </p>
                </ScrollArea>
              )}
            </div>
          </div>

          {/* Rejection Form */}
          {showRejectForm && (
            <div className="space-y-2 border border-red-500/20 rounded-lg p-3 bg-red-500/5">
              <p className="text-sm font-medium text-red-400">Rejection Reason (required for audit)</p>
              <Textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                className="h-24 resize-none text-sm"
                placeholder="Describe why this AI output is being rejected (min. 10 characters)..."
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={handleReject}
                  disabled={isLoading || rejectReason.length < 10}
                >
                  Confirm Rejection
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setShowRejectForm(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {/* Approved/Rejected Display */}
          {!isPending && (
            <div className="rounded-lg border border-muted/60 p-3 bg-muted/10 space-y-1">
              <p className="text-xs text-muted-foreground">
                Decision by{" "}
                <span className="text-foreground font-medium">
                  {approval.reviewer_name || "Unknown"}
                </span>{" "}
                {approval.decided_at && formatDistanceToNow(new Date(approval.decided_at), { addSuffix: true })}
              </p>
              {approval.human_edited_content && (
                <p className="text-xs text-blue-400 mt-1">
                  ✏️ Content was edited before approval
                </p>
              )}
              {approval.rejection_reason && (
                <p className="text-xs text-red-400 mt-1">
                  Reason: {approval.rejection_reason}
                </p>
              )}
            </div>
          )}

          {/* Workflow Context */}
          {approval.workflow_context && (
            <details className="text-xs">
              <summary className="cursor-pointer text-muted-foreground hover:text-foreground transition-colors">
                Workflow Context
              </summary>
              <pre className="mt-2 p-2 rounded bg-muted/30 overflow-auto text-[11px] leading-relaxed text-muted-foreground">
                {JSON.stringify(approval.workflow_context, null, 2)}
              </pre>
            </details>
          )}
        </CardContent>
      )}
    </Card>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ApprovalsPage() {
  const { data: pendingData, isLoading: pendingLoading } = usePendingApprovals();
  const { data: allData, isLoading: allLoading } = useAllApprovals();

  const pendingApprovals: Approval[] = (pendingData as any)?.data ?? [];
  const allApprovals: Approval[] = (allData as any)?.data ?? [];
  const pendingTotal: number = (pendingData as any)?.total ?? 0;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-primary" />
            Human-in-the-Loop Approvals
          </h2>
          <p className="text-muted-foreground">
            Review, edit, or reject AI-generated outputs before they reach external recipients.
          </p>
        </div>

        {pendingTotal > 0 && (
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500" />
            </span>
            <span className="text-sm text-amber-400 font-medium">
              {pendingTotal} awaiting review
            </span>
          </div>
        )}
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Pending Review", value: allApprovals.filter(a => a.status === "pending_approval").length, color: "text-amber-400" },
          { label: "Approved", value: allApprovals.filter(a => a.status === "approved").length, color: "text-emerald-400" },
          { label: "Edited & Approved", value: allApprovals.filter(a => a.status === "edited").length, color: "text-blue-400" },
          { label: "Rejected", value: allApprovals.filter(a => a.status === "rejected").length, color: "text-red-400" },
        ].map((kpi) => (
          <Card key={kpi.label} className="border-muted/60">
            <CardContent className="pt-4 pb-3">
              <p className="text-xs text-muted-foreground">{kpi.label}</p>
              <p className={`text-3xl font-bold mt-1 ${kpi.color}`}>{kpi.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Tabs: Pending Queue vs Full Audit Log */}
      <Tabs defaultValue="pending">
        <TabsList>
          <TabsTrigger value="pending" className="gap-2">
            <Clock className="h-4 w-4" />
            Pending Review
            {pendingTotal > 0 && (
              <Badge className="ml-1 bg-amber-500/20 text-amber-400 border-amber-500/30 shadow-none text-[10px]">
                {pendingTotal}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-2">
            <ShieldCheck className="h-4 w-4" />
            Audit Log
          </TabsTrigger>
        </TabsList>

        {/* Pending Queue Tab */}
        <TabsContent value="pending" className="mt-4 space-y-3">
          {pendingLoading ? (
            <Card className="border-muted/60">
              <CardContent className="py-12 text-center text-muted-foreground">
                <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 opacity-50" />
                Loading approval queue...
              </CardContent>
            </Card>
          ) : pendingApprovals.length === 0 ? (
            <Card className="border-muted/60">
              <CardContent className="py-16 text-center space-y-3">
                <Check className="h-10 w-10 mx-auto text-emerald-500/50" />
                <p className="text-muted-foreground font-medium">All caught up!</p>
                <p className="text-sm text-muted-foreground">
                  No workflows are currently awaiting human review. New approvals will appear here automatically.
                </p>
              </CardContent>
            </Card>
          ) : (
            pendingApprovals.map((approval) => (
              <ApprovalCard key={approval.id} approval={approval} />
            ))
          )}
        </TabsContent>

        {/* Audit Log Tab */}
        <TabsContent value="history" className="mt-4 space-y-3">
          {allLoading ? (
            <p className="text-sm text-muted-foreground">Loading audit log...</p>
          ) : (
            allApprovals.map((approval) => (
              <ApprovalCard key={approval.id} approval={approval} />
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
