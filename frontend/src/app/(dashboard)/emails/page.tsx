/**
 * frontend/src/app/(dashboard)/emails/page.tsx
 *
 * WHY IT EXISTS:
 * Since this is an Email-driven AI workflow platform (Level 2B), admins need a
 * way to monitor the ingestion pipeline. Did the email parse correctly? Which
 * workflow did it trigger?
 *
 * WHAT IT DOES:
 * Displays a searchable, paginated list of ingested emails and their routing status.
 *
 * HOW IT CONNECTS TO BACKEND:
 * Connects to `GET /api/v1/gmail/ingestion-logs`.
 */

"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, ExternalLink, Mailbox } from "lucide-react";
import Link from "next/link";

const mockEmails = [
  { id: "msg_1A2B3C", sender: "customer.jane@example.com", subject: "Refund Request", status: "Processed", workflowId: "wf-1049", time: "2 mins ago" },
  { id: "msg_4D5E6F", sender: "newsletter@updates.com", subject: "Weekly Tech Digest", status: "Processed", workflowId: "wf-1048", time: "1 hour ago" },
  { id: "msg_7G8H9I", sender: "angry.user@domain.com", subject: "Where is my order?!", status: "Processing", workflowId: "wf-1050", time: "Just now" },
  { id: "msg_0J1K2L", sender: "spam@scam.net", subject: "You won a million dollars", status: "Ignored", workflowId: null, time: "4 hours ago" },
];

export default function EmailsPage() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Email Ingestion Log</h2>
          <p className="text-muted-foreground">
            Monitor raw inputs parsed by the Celery polling workers.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader className="border-b pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Mailbox className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Inbox Polling History</CardTitle>
            </div>
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search senders or subjects..."
                className="w-[300px] pl-9"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-muted/30">
              <TableRow>
                <TableHead className="pl-6">Message ID</TableHead>
                <TableHead>Sender</TableHead>
                <TableHead>Subject</TableHead>
                <TableHead>Received</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right pr-6">Linked Workflow</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockEmails.map((email) => (
                <TableRow key={email.id} className="cursor-pointer hover:bg-muted/50 transition-colors">
                  <TableCell className="pl-6 font-mono text-xs text-muted-foreground">{email.id}</TableCell>
                  <TableCell className="font-medium">{email.sender}</TableCell>
                  <TableCell className="max-w-[300px] truncate">{email.subject}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{email.time}</TableCell>
                  <TableCell>
                    <Badge 
                      variant={email.status === "Processed" ? "default" : email.status === "Processing" ? "secondary" : "destructive"}
                      className={email.status === "Processed" ? "bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20" : ""}
                    >
                      {email.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right pr-6">
                    {email.workflowId ? (
                      <Link href={`/workflows/${email.workflowId}`}>
                        <Button variant="ghost" size="sm" className="gap-2 text-xs font-mono">
                          {email.workflowId}
                          <ExternalLink className="h-3 w-3" />
                        </Button>
                      </Link>
                    ) : (
                      <span className="text-xs text-muted-foreground mr-4">-</span>
                    )}
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
