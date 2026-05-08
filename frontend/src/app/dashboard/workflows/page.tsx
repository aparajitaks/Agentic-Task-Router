/**
 * frontend/src/app/(dashboard)/workflows/page.tsx
 *
 * WHY IT EXISTS:
 * Serves as the high-level orchestration monitoring page.
 *
 * WHAT IT DOES:
 * Embeds the React Flow DAG (`WorkflowGraph`) and renders a data table of
 * recent workflow executions.
 *
 * HOW IT CONNECTS TO BACKEND:
 * Queries `GET /api/v1/tasks` to populate the recent executions table.
 */

"use client";

import { WorkflowGraph } from "./components/workflow-graph";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useTasks } from "@/hooks/use-tasks";
import { formatDistanceToNow } from "date-fns";
import { Eye, RefreshCw } from "lucide-react";
import Link from "next/link";

export default function WorkflowsPage() {
  const { data: response, isLoading, isError } = useTasks(1, 10);
  const tasks = response?.data || [];
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Active Executions</h2>
          <p className="text-muted-foreground">
            Live visualization of LangGraph autonomous agent loops.
          </p>
        </div>
        <Button variant="outline" size="sm" className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Refresh Nodes
        </Button>
      </div>

      <WorkflowGraph />

      <Card>
        <CardHeader>
          <CardTitle>Recent Orchestrations</CardTitle>
          <CardDescription>
            A log of all workflows routed through the system in the last hour.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Workflow ID</TableHead>
                <TableHead>Trigger</TableHead>
                <TableHead>Selected Agent</TableHead>
                <TableHead>Tools Executed</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">Loading workflows...</TableCell>
                </TableRow>
              ) : tasks.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">No workflows found.</TableCell>
                </TableRow>
              ) : (
                tasks.map((wf: any) => (
                  <TableRow key={wf.id}>
                    <TableCell className="font-medium">{wf.id.split('-')[0]}</TableCell>
                    <TableCell>{wf.source}</TableCell>
                    <TableCell>{wf.result_data?.agent || "Router"}</TableCell>
                    <TableCell>
                      <div className="flex gap-1 flex-wrap">
                        {wf.result_data?.tools_used ? wf.result_data.tools_used.map((t: string) => (
                          <Badge key={t} variant="secondary" className="text-[10px]">{t}</Badge>
                        )) : <span className="text-muted-foreground text-xs">None</span>}
                      </div>
                    </TableCell>
                    <TableCell>{formatDistanceToNow(new Date(wf.created_at), { addSuffix: true })}</TableCell>
                    <TableCell>
                      <Badge variant={wf.status === "PROCESSING" ? "default" : wf.status === "COMPLETED" ? "outline" : "destructive"} className={wf.status === "PROCESSING" ? "bg-blue-500 hover:bg-blue-600" : ""}>
                        {wf.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Link href={`/workflows/${wf.id}`}>
                        <Button variant="ghost" size="icon">
                          <Eye className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
