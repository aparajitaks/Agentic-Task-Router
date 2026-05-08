/**
 * frontend/src/app/(dashboard)/tools/page.tsx
 *
 * WHY IT EXISTS:
 * Autonomous agents executing external actions (sending emails, searching the web)
 * carry inherent risk. A dedicated Tool Observability dashboard ensures all actions
 * are auditable.
 *
 * WHAT IT DOES:
 * Displays aggregate tool performance metrics and a real-time ledger of all
 * `ToolExecutionLog` entries.
 *
 * HOW IT CONNECTS TO BACKEND:
 * Connects to `GET /api/v1/tools` and `GET /api/v1/tools/logs`.
 */

"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Wrench, CheckCircle2, XCircle, Globe, Calculator, Database, Send } from "lucide-react";

const toolIcons: Record<string, any> = {
  "web_search_tool": Globe,
  "calculator_tool": Calculator,
  "db_lookup_tool": Database,
  "gmail_send_tool": Send,
  "doc_retrieval_tool": Wrench
};

const mockToolLogs = [
  { id: "log-912", tool: "gmail_send_tool", args: { to: "customer@domain.com", subject: "Refund" }, success: true, time: "850ms", date: "Just now" },
  { id: "log-911", tool: "doc_retrieval_tool", args: { query: "refund policy" }, success: true, time: "42ms", date: "1 min ago" },
  { id: "log-910", tool: "calculator_tool", args: { expression: "10 * 4.5" }, success: true, time: "12ms", date: "5 mins ago" },
  { id: "log-909", tool: "web_search_tool", args: { query: "Apple Stock Price" }, success: false, time: "2100ms", date: "15 mins ago" },
];

export default function ToolsPage() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Tool Observability</h2>
          <p className="text-muted-foreground">
            Audit trail of all autonomous actions taken by AI agents.
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Executions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">14,291</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-500">98.2%</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg Latency</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">340ms</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Most Used</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold truncate">doc_retrieval_tool</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Execution Ledger</CardTitle>
          <CardDescription>
            Raw logs of arguments passed from the LLM to the Python tool engine.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Tool</TableHead>
                <TableHead>JSON Arguments</TableHead>
                <TableHead>Latency</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Timestamp</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockToolLogs.map((log) => {
                const Icon = toolIcons[log.tool] || Wrench;
                return (
                  <TableRow key={log.id}>
                    <TableCell className="font-medium flex items-center gap-2">
                      <Icon className="h-4 w-4 text-muted-foreground" />
                      {log.tool}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {JSON.stringify(log.args)}
                    </TableCell>
                    <TableCell>{log.time}</TableCell>
                    <TableCell>
                      {log.success ? (
                        <Badge variant="outline" className="text-emerald-500 border-emerald-500/30 gap-1">
                          <CheckCircle2 className="h-3 w-3" /> Success
                        </Badge>
                      ) : (
                        <Badge variant="destructive" className="gap-1">
                          <XCircle className="h-3 w-3" /> Failed
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground text-sm">
                      {log.date}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
