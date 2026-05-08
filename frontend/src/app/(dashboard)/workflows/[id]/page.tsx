/**
 * frontend/src/app/(dashboard)/workflows/[id]/page.tsx
 *
 * WHY IT EXISTS:
 * When an autonomous workflow fails or behaves unexpectedly, engineers need a
 * microscopic view into the execution. This page acts as the LangSmith-style trace.
 *
 * WHAT IT DOES:
 * Displays a granular timeline of the workflow, showing exact prompts,
 * tool inputs/outputs, and final generations via JSON and text viewers.
 *
 * HOW IT CONNECTS TO BACKEND:
 * Will query `GET /api/v1/tasks/{id}` and `GET /api/v1/tools/logs?task_id={id}`.
 */

"use client";

import { use } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ArrowLeft, Bot, CheckCircle2, Clock, TerminalSquare, Wrench } from "lucide-react";
import Link from "next/link";

export default function WorkflowDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  // Using React.use to unwrap Next.js 15 async route params
  const { id } = use(params);

  // Mock trace data representing LangGraph WorkflowState
  const trace = {
    id,
    status: "Completed",
    agent: "Reply Generator",
    duration: "8.4s",
    input: "Customer: I need a refund for my order #88392. It arrived broken.",
    finalOutput: "Dear Customer,\n\nI apologize that order #88392 arrived broken. According to our policy, since it was reported within 30 days, I have processed a full refund to your original payment method.\n\nBest,\nSupport Team",
    steps: [
      { type: "router", text: "Analyzing input to determine agent route...", time: "+0.1s" },
      { type: "agent", text: "Selected: Reply Generator Agent", time: "+0.3s" },
      { type: "tool_call", text: "doc_retrieval_tool({\"query\": \"refund policy broken items\"})", time: "+2.1s" },
      { type: "tool_result", text: "Policy: Refunds allowed within 30 days for broken items.", time: "+4.5s" },
      { type: "agent", text: "Generating final response based on tool context...", time: "+6.2s" },
      { type: "complete", text: "Workflow finished and state committed to DB.", time: "+8.4s" },
    ]
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header Area */}
      <div className="flex items-center gap-4">
        <Link href="/workflows">
          <Button variant="outline" size="icon" className="h-8 w-8">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold tracking-tight">Trace: {id}</h2>
            <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
              {trace.status}
            </Badge>
          </div>
          <p className="text-muted-foreground text-sm flex items-center gap-2 mt-1">
            <Bot className="h-4 w-4" /> {trace.agent}
            <span className="mx-2 text-muted-foreground/30">•</span>
            <Clock className="h-4 w-4" /> {trace.duration}
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Execution Timeline (Left Column) */}
        <Card className="md:col-span-1 border-muted/60 shadow-none">
          <CardHeader>
            <CardTitle className="text-lg">Execution Timeline</CardTitle>
            <CardDescription>Step-by-step LangGraph node trace.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 relative before:absolute before:inset-0 before:ml-2 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-border before:to-transparent">
              {trace.steps.map((step, i) => (
                <div key={i} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                  <div className="flex items-center justify-center w-5 h-5 rounded-full border bg-background shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 text-muted-foreground">
                    {step.type === "tool_call" ? <Wrench className="h-3 w-3 text-indigo-500" /> : 
                     step.type === "complete" ? <CheckCircle2 className="h-3 w-3 text-emerald-500" /> :
                     <TerminalSquare className="h-3 w-3" />}
                  </div>
                  <div className="w-[calc(100%-2.5rem)] md:w-[calc(50%-1.25rem)] p-3 rounded border bg-muted/30">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">{step.type}</span>
                      <span className="text-[10px] text-muted-foreground font-mono">{step.time}</span>
                    </div>
                    <p className="text-xs text-foreground font-mono break-words">{step.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* State Inspector (Right Column) */}
        <Card className="md:col-span-2 border-muted/60 shadow-none">
          <CardHeader>
            <CardTitle className="text-lg">State Inspector</CardTitle>
            <CardDescription>Deep dive into the LLM context windows.</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Tabs defaultValue="output" className="w-full">
              <div className="px-6 pb-2">
                <TabsList className="grid w-full grid-cols-3 bg-muted/50">
                  <TabsTrigger value="input">Raw Input</TabsTrigger>
                  <TabsTrigger value="output">Final Generation</TabsTrigger>
                  <TabsTrigger value="json">State JSON</TabsTrigger>
                </TabsList>
              </div>
              
              <TabsContent value="input" className="p-0 border-t mt-0">
                <ScrollArea className="h-[400px] w-full bg-muted/20 p-6 rounded-b-xl">
                  <pre className="text-sm font-mono text-muted-foreground whitespace-pre-wrap">
                    {trace.input}
                  </pre>
                </ScrollArea>
              </TabsContent>
              
              <TabsContent value="output" className="p-0 border-t mt-0">
                <ScrollArea className="h-[400px] w-full bg-muted/20 p-6 rounded-b-xl">
                  <pre className="text-sm font-mono text-foreground whitespace-pre-wrap">
                    {trace.finalOutput}
                  </pre>
                </ScrollArea>
              </TabsContent>

              <TabsContent value="json" className="p-0 border-t mt-0">
                <ScrollArea className="h-[400px] w-full bg-black p-6 rounded-b-xl">
                  <pre className="text-xs font-mono text-emerald-400 whitespace-pre-wrap">
                    {JSON.stringify(trace, null, 2)}
                  </pre>
                </ScrollArea>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
