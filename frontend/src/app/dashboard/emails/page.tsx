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
 * Connects to `GET /api/v1/gmail/emails`.
 */

"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { formatDistanceToNow } from "date-fns";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, ExternalLink, Mailbox } from "lucide-react";
import Link from "next/link";

export default function EmailsPage() {
  const [emails, setEmails] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEmails = async () => {
      try {
        const response = await axios.get("http://localhost:8000/api/v1/gmail/emails", {
          headers: { "X-Clerk-ID": "demo_user_123" }
        });
        setEmails(response.data.data);
      } catch (e) {
        console.error("Failed to fetch emails", e);
      } finally {
        setLoading(false);
      }
    };
    fetchEmails();
  }, []);
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
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-10 text-muted-foreground">
                    Loading ingested emails...
                  </TableCell>
                </TableRow>
              ) : emails.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-10 text-muted-foreground">
                    No emails ingested yet. Try syncing your inbox.
                  </TableCell>
                </TableRow>
              ) : (
                emails.map((email) => (
                  <TableRow key={email.id} className="cursor-pointer hover:bg-muted/50 transition-colors">
                    <TableCell className="pl-6 font-mono text-xs text-muted-foreground">{email.gmail_message_id}</TableCell>
                    <TableCell className="font-medium">{email.sender}</TableCell>
                    <TableCell className="max-w-[300px] truncate">{email.subject}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(email.received_at), { addSuffix: true })}
                    </TableCell>
                    <TableCell>
                      <Badge 
                        variant={email.status === "QUEUED" || email.status === "Processing" ? "secondary" : email.status === "FAILED" ? "destructive" : "default"}
                        className={email.status === "SUCCESS" || email.status === "Processed" ? "bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20" : ""}
                      >
                        {email.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right pr-6">
                      {email.task_id ? (
                        <Link href={`/dashboard/workflows/${email.task_id}`}>
                          <Button variant="ghost" size="sm" className="gap-2 text-xs font-mono">
                            {email.task_id.slice(0, 8)}
                            <ExternalLink className="h-3 w-3" />
                          </Button>
                        </Link>
                      ) : (
                        <span className="text-xs text-muted-foreground mr-4">-</span>
                      )}
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
