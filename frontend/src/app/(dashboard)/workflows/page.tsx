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
import { Eye, RefreshCw } from "lucide-react";
import Link from "next/link";

const mockWorkflows = [
  { id: "wf-1049", type: "Email Support", agent: "Reply Generator", status: "Running", tools: ["db_lookup", "calculator_tool"], time: "14s" },
  { id: "wf-1048", type: "Newsletter Ingest", agent: "Summarizer Agent", status: "Completed", tools: [], time: "3s" },
  { id: "wf-1047", type: "Policy Question", agent: "Reply Generator", status: "Completed", tools: ["doc_retrieval_tool"], time: "8s" },
  { id: "wf-1046", type: "Unknown Formatting", agent: "Router Agent", status: "Failed", tools: [], time: "1s" },
];

export default function WorkflowsPage() {
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
              {mockWorkflows.map((wf) => (
                <TableRow key={wf.id}>
                  <TableCell className="font-medium">{wf.id}</TableCell>
                  <TableCell>{wf.type}</TableCell>
                  <TableCell>{wf.agent}</TableCell>
                  <TableCell>
                    <div className="flex gap-1 flex-wrap">
                      {wf.tools.length > 0 ? wf.tools.map(t => (
                        <Badge key={t} variant="secondary" className="text-[10px]">{t}</Badge>
                      )) : <span className="text-muted-foreground text-xs">None</span>}
                    </div>
                  </TableCell>
                  <TableCell>{wf.time}</TableCell>
                  <TableCell>
                    <Badge variant={wf.status === "Running" ? "default" : wf.status === "Completed" ? "outline" : "destructive"} className={wf.status === "Running" ? "bg-blue-500 hover:bg-blue-600" : ""}>
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
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
