/**
 * frontend/src/app/(dashboard)/agents/page.tsx
 *
 * WHY IT EXISTS:
 * In a multi-agent system, we need to know which agents are doing the heavy
 * lifting, which ones are failing, and how much time they consume.
 *
 * WHAT IT DOES:
 * Displays cards for each registered agent with its specific throughput,
 * success rate, and active status.
 *
 * HOW IT CONNECTS TO BACKEND:
 * N/A - Mocked for visual demonstration of the SaaS dashboard architecture.
 */

"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bot, Network, Edit3, FastForward } from "lucide-react";
import { Progress } from "@/components/ui/progress";

const agents = [
  {
    name: "Router Agent",
    description: "Determines intent and routes tasks to specialized agents.",
    icon: Network,
    status: "Active",
    tasks: 14291,
    successRate: 99.8,
    avgLatency: "110ms",
    model: "llama-3.3-70b",
  },
  {
    name: "Summarizer Agent",
    description: "Condenses long text and extracts key entities.",
    icon: FastForward,
    status: "Active",
    tasks: 4392,
    successRate: 97.2,
    avgLatency: "450ms",
    model: "llama-3.3-70b",
  },
  {
    name: "Reply Generator Agent",
    description: "Drafts professional emails and utilizes tools for context.",
    icon: Edit3,
    status: "Active",
    tasks: 9899,
    successRate: 95.5,
    avgLatency: "1.2s",
    model: "llama-3.3-70b",
  }
];

export default function AgentsPage() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Agent Fleet</h2>
          <p className="text-muted-foreground">
            Manage and monitor the performance of specialized AI agents.
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {agents.map((agent) => (
          <Card key={agent.name} className="relative overflow-hidden group">
            <div className="absolute inset-x-0 top-0 h-1 bg-primary transform origin-left transition-transform duration-300 scale-x-0 group-hover:scale-x-100" />
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10 text-primary">
                    <agent.icon className="h-6 w-6" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{agent.name}</CardTitle>
                    <Badge variant="outline" className="mt-1 text-[10px] uppercase font-mono bg-muted/50">
                      {agent.model}
                    </Badge>
                  </div>
                </div>
                <Badge className="bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 shadow-none border-none">
                  {agent.status}
                </Badge>
              </div>
              <CardDescription className="pt-4">{agent.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Total Invocations</span>
                    <p className="font-semibold text-lg">{agent.tasks.toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Avg Latency</span>
                    <p className="font-semibold text-lg">{agent.avgLatency}</p>
                  </div>
                </div>
                
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Success Rate</span>
                    <span className="font-medium text-emerald-500">{agent.successRate}%</span>
                  </div>
                  <Progress value={agent.successRate} className="h-1.5" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
