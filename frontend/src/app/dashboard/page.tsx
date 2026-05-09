/**
 * frontend/src/app/dashboard/page.tsx
 * 
 * WHY IT EXISTS:
 * This is the nerve center for the end-user. It transforms engineering
 * metrics into personal productivity insights. 
 *
 * WHAT IT DOES:
 * - Displays user-personalized KPIs (emails processed, time saved).
 * - Shows active automation status (Gmail connection, agent health).
 * - Provides a "Action Required" section for HITL approvals.
 * - Visualizes recent AI activity with high-end area charts.
 * - Offers a "Get Started" guide for new users.
 *
 * HOW IT CONNECTS:
 * - Polls user-scoped endpoints (GET /tasks, GET /approvals/pending).
 */

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import { 
  Bot, 
  Mail, 
  ShieldCheck, 
  Zap, 
  ArrowUpRight, 
  Clock, 
  CheckCircle2, 
  AlertCircle,
  Plus,
  RefreshCw,
  Search,
  Settings,
  ChevronRight,
  Sparkles
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button, buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from "recharts";

// Mock Data - In a real app, this comes from React Query hooks
const DATA = [
  { name: "00:00", count: 45 },
  { name: "04:00", count: 32 },
  { name: "08:00", count: 124 },
  { name: "12:00", count: 210 },
  { name: "16:00", count: 185 },
  { name: "20:00", count: 98 },
  { name: "24:00", count: 54 },
];

export default function WorkspaceDashboard() {
  const [isGmailConnected, setIsGmailConnected] = useState(false);
  const [pendingApprovals, setPendingApprovals] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);
  const [userEmail, setUserEmail] = useState("Not connected");

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const config = { headers: { "X-Clerk-ID": "demo_user_123" } };
        
        // Fetch Gmail status
        const gmailRes: any = await apiClient.get("/gmail/status", config);
        setIsGmailConnected(gmailRes.connected);
        
        // Fetch Pending Approvals
        const approvalsRes: any = await apiClient.get("/approvals/pending", config);
        setPendingApprovals(approvalsRes.total || 0);

        // Fetch User Info
        const userRes: any = await apiClient.get("/users/me", config);
        setUserEmail(userRes.email);
      } catch (e) {
        console.error("Dashboard data fetch failed", e);
      }
    };
    fetchStats();
  }, []);

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      await apiClient.post("/gmail/sync", {}, {
        headers: { "X-Clerk-ID": "demo_user_123" }
      });
      // Refresh logic would go here
    } catch (e) {
      console.error("Sync failed", e);
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      
      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1">
          <Badge variant="outline" className="text-[10px] uppercase tracking-widest text-primary border-primary/20 bg-primary/5">
            Personal Workspace
          </Badge>
          <h2 className="text-3xl font-bold tracking-tight">Good Morning, User.</h2>
          <p className="text-muted-foreground">Your AI assistants have processed 12 emails while you were away.</p>
        </div>

        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            className="h-9 gap-2"
            onClick={handleSync}
            disabled={isSyncing}
          >
            <RefreshCw className={cn("h-3.5 w-3.5", isSyncing && "animate-spin")} />
            {isSyncing ? "Syncing..." : "Sync Now"}
          </Button>
          <Button size="sm" className="h-9 gap-2 shadow-lg shadow-primary/20">
            <Plus className="h-3.5 w-3.5" />
            New Workflow
          </Button>
        </div>
      </div>

      {/* ── Top Row: Critical Status ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        {/* Gmail Connection Status */}
        <Card className="bg-gradient-to-br from-background to-muted/30 border-muted/60 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:scale-110 transition-transform">
            <Mail className="h-24 w-24" />
          </div>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-4">
              <div className="h-10 w-10 rounded-lg bg-red-500/10 flex items-center justify-center">
                <Mail className="h-5 w-5 text-red-500" />
              </div>
              {isGmailConnected ? (
                <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">Connected</Badge>
              ) : (
                <Badge variant="destructive">Disconnected</Badge>
              )}
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">Active Connection</p>
              <p className="text-lg font-bold">{isGmailConnected ? userEmail : "No Account Linked"}</p>
            </div>
            <Button variant="ghost" size="sm" className="w-full mt-4 h-8 text-xs text-muted-foreground border border-dashed hover:border-muted-foreground/40">
              Connection Settings
            </Button>
          </CardContent>
        </Card>

        {/* Approvals Pending (HITL) */}
        <Card className="bg-gradient-to-br from-background to-muted/30 border-muted/60 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:scale-110 transition-transform">
            <ShieldCheck className="h-24 w-24" />
          </div>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-4">
              <div className="h-10 w-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <ShieldCheck className="h-5 w-5 text-amber-500" />
              </div>
              <Badge variant="outline" className="text-amber-500 border-amber-500/30">Needs Review</Badge>
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">Action Items</p>
              <p className="text-lg font-bold">{pendingApprovals} Pending Approvals</p>
            </div>
            <Link 
              href="/dashboard/approvals" 
              className={cn(
                buttonVariants({ variant: "secondary", size: "sm" }),
                "w-full mt-4 h-8 text-xs bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 border-amber-500/20 gap-2"
              )}
            >
              Open Approval Inbox
              <ArrowUpRight className="h-3 w-3" />
            </Link>
          </CardContent>
        </Card>

        {/* System Health */}
        <Card className="bg-gradient-to-br from-background to-muted/30 border-muted/60 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:scale-110 transition-transform">
            <Zap className="h-24 w-24" />
          </div>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-4">
              <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Zap className="h-5 w-5 text-blue-500" />
              </div>
              <Badge className="bg-blue-500/10 text-blue-500 border-blue-500/20">Active</Badge>
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">Automation Engine</p>
              <p className="text-lg font-bold">12/12 Agents Online</p>
            </div>
            <div className="mt-5 space-y-1">
              <div className="flex justify-between text-[10px] font-bold uppercase text-muted-foreground">
                <span>Task Throughput</span>
                <span>98%</span>
              </div>
              <Progress value={98} className="h-1 bg-muted" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Middle Section: Chart & Activity ────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Productivity Chart */}
        <Card className="lg:col-span-2 border-muted/60">
          <CardHeader className="flex flex-row items-center justify-between">
            <div className="space-y-1">
              <CardTitle className="text-lg">AI Automation Volume</CardTitle>
              <CardDescription>Processed vs Human-intervened tasks (24h)</CardDescription>
            </div>
            <div className="flex gap-2">
              <Badge variant="outline" className="bg-primary/5 text-primary">Live</Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-4 h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={DATA}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--muted)/0.4)" />
                <XAxis 
                  dataKey="name" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{fontSize: 10, fill: 'hsl(var(--muted-foreground))'}} 
                  dy={10}
                />
                <YAxis 
                  hide 
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--muted))', borderRadius: '8px', fontSize: '12px' }}
                  itemStyle={{ color: 'hsl(var(--primary))' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="count" 
                  stroke="hsl(var(--primary))" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorCount)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Recent Insights */}
        <Card className="border-muted/60">
          <CardHeader>
            <CardTitle className="text-lg">AI Insights</CardTitle>
            <CardDescription>Generated from your recent activity.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div className="flex gap-4">
                <div className="h-8 w-8 rounded bg-emerald-500/10 flex items-center justify-center shrink-0">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium">Efficiency Boost</p>
                  <p className="text-xs text-muted-foreground">AI has saved you ~2.4 hours of inbox management this week.</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="h-8 w-8 rounded bg-blue-500/10 flex items-center justify-center shrink-0">
                  <AlertCircle className="h-4 w-4 text-blue-500" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium">New Pattern Detected</p>
                  <p className="text-xs text-muted-foreground">Increase in support-related emails. Suggesting "Priority Inbox" workflow.</p>
                </div>
              </div>
            </div>
            <Separator />
            <div className="space-y-3">
              <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Recommended For You</p>
              <div className="rounded-lg border bg-muted/20 p-3 flex items-center justify-between group hover:bg-muted/40 transition-colors cursor-pointer">
                <div className="flex items-center gap-3">
                  <Sparkles className="h-4 w-4 text-primary" />
                  <span className="text-sm font-medium">Draft Weekly Report</span>
                </div>
                <Plus className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Bottom Section: Active Workflows ────────────────────────────────── */}
      <Card className="border-muted/60 overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg">Active Automations</CardTitle>
            <CardDescription>Workflows currently monitoring your workspace.</CardDescription>
          </div>
          <Button variant="ghost" size="sm" className="text-xs gap-2">
            View All <ChevronRight className="h-3 w-3" />
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y border-t bg-muted/5">
            {[
              { name: "Morning Briefing", type: "Summarizer", status: "Running", calls: 12, last: "2m ago" },
              { name: "Support Auto-Reply", type: "Reply Generator", status: "HITL Paused", calls: 3, last: "15m ago" },
              { name: "Invoice Extractor", type: "Task Agent", status: "Running", calls: 8, last: "1h ago" },
            ].map((wf, idx) => (
              <div key={idx} className="flex items-center justify-between px-6 py-4 hover:bg-muted/10 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-lg bg-background border flex items-center justify-center">
                    <Bot className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-bold">{wf.name}</p>
                    <p className="text-[11px] text-muted-foreground">{wf.type}</p>
                  </div>
                </div>
                <div className="flex items-center gap-8">
                  <div className="hidden md:block text-right">
                    <p className="text-xs font-medium">{wf.calls} Tool Calls</p>
                    <p className="text-[10px] text-muted-foreground">Processed today</p>
                  </div>
                  <div className="hidden md:block text-right">
                    <p className="text-xs font-medium">{wf.last}</p>
                    <p className="text-[10px] text-muted-foreground">Last active</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className={`text-[10px] ${wf.status === 'Running' ? 'text-emerald-500 border-emerald-500/20 bg-emerald-500/5' : 'text-amber-500 border-amber-500/20 bg-amber-500/5'}`}>
                      {wf.status}
                    </Badge>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <Settings className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}


