/**
 * frontend/src/app/(dashboard)/templates/page.tsx
 *
 * WHY IT EXISTS:
 * To move away from a "configure from scratch" model to a "one-click deploy" 
 * model. This makes the product feel much more accessible to non-engineers.
 *
 * WHAT IT DOES:
 * - Renders a grid of pre-built AI workflow templates.
 * - Categorizes templates (Productivity, Support, Finance, etc.).
 * - Shows visual indicators of what agents/tools are used in each.
 * - Provides a "Deploy" flow for each template.
 */

"use client";

import { useState } from "react";
import { 
  Plus, 
  Search, 
  Filter, 
  Sparkles, 
  Mail, 
  ShieldCheck, 
  Zap, 
  Bot, 
  Wrench,
  ChevronRight,
  Info
} from "lucide-react";

import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from "@/components/ui/tabs";
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const TEMPLATES = [
  {
    id: "summarizer",
    category: "productivity",
    name: "24h Inbox Briefing",
    desc: "Aggregates all incoming emails from the last 24 hours into a concise, actionable summary.",
    agents: ["Summarizer Agent"],
    tools: ["Gmail Reader"],
    complexity: "Low",
    hitl: "Optional",
    installed: true
  },
  {
    id: "reply_bot",
    category: "support",
    name: "Intelligent Auto-Reply",
    desc: "Drafts high-quality responses to common inquiries. Pauses for your approval before sending.",
    agents: ["Router Agent", "Reply Generator"],
    tools: ["Gmail Writer", "Web Search"],
    complexity: "Medium",
    hitl: "Always",
    installed: false
  },
  {
    id: "invoice_bot",
    category: "finance",
    name: "Invoice & Receipt Extractor",
    desc: "Automatically identifies financial documents and extracts key metadata into a structured log.",
    agents: ["Extraction Agent"],
    tools: ["Gmail Reader", "DB Writer"],
    complexity: "High",
    hitl: "Optional",
    installed: false
  },
  {
    id: "priority_alert",
    category: "productivity",
    name: "Urgent Sentiment Guard",
    desc: "Analyzes sentiment of incoming mail and flags negative or urgent messages immediately.",
    agents: ["Router Agent"],
    tools: ["Gmail Reader", "Slack Notify"],
    complexity: "Low",
    hitl: "None",
    installed: true
  },
  {
    id: "knowledge_base",
    category: "support",
    name: "RAG Support Assistant",
    desc: "Queries your internal documentation to answer customer questions automatically.",
    agents: ["Router Agent", "Knowledge Agent"],
    tools: ["Vector DB", "Gmail Writer"],
    complexity: "High",
    hitl: "Always",
    installed: false
  }
];

export default function TemplateMarketplace() {
  const [activeTab, setActiveTab] = useState("all");

  const filteredTemplates = activeTab === "all" 
    ? TEMPLATES 
    : TEMPLATES.filter(t => t.category === activeTab);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-3xl font-bold tracking-tight">Workflow Templates</h2>
          <p className="text-muted-foreground">Deploy pre-configured AI agents in one click.</p>
        </div>
        <Button className="h-10 gap-2 shadow-lg shadow-primary/20">
          <Plus className="h-4 w-4" />
          Create Custom
        </Button>
      </div>

      {/* ── Search & Filter ─────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search templates..." className="pl-10 h-10 bg-muted/20 border-muted/60 focus-visible:ring-primary/30" />
        </div>
        <Tabs defaultValue="all" onValueChange={setActiveTab} className="w-full md:w-auto">
          <TabsList className="grid grid-cols-4 md:flex h-10 bg-muted/20 border-muted/60">
            <TabsTrigger value="all" className="text-xs">All</TabsTrigger>
            <TabsTrigger value="productivity" className="text-xs">Productivity</TabsTrigger>
            <TabsTrigger value="support" className="text-xs">Support</TabsTrigger>
            <TabsTrigger value="finance" className="text-xs">Finance</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* ── Template Grid ───────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTemplates.map((t) => (
          <Card key={t.id} className="group border-muted/60 hover:border-primary/50 transition-all duration-300 bg-gradient-to-br from-background to-muted/10 overflow-hidden flex flex-col">
            <CardHeader className="pb-4">
              <div className="flex items-start justify-between">
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  {t.category === 'productivity' && <Sparkles className="h-5 w-5 text-primary" />}
                  {t.category === 'support' && <Mail className="h-5 w-5 text-primary" />}
                  {t.category === 'finance' && <Zap className="h-5 w-5 text-primary" />}
                </div>
                {t.installed && (
                  <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 gap-1 text-[10px]">
                    Installed
                  </Badge>
                )}
              </div>
              <div className="space-y-1 pt-4">
                <CardTitle className="text-lg group-hover:text-primary transition-colors">{t.name}</CardTitle>
                <CardDescription className="line-clamp-2 text-xs leading-relaxed">{t.desc}</CardDescription>
              </div>
            </CardHeader>
            
            <CardContent className="flex-grow space-y-4">
              <div className="flex flex-wrap gap-1.5">
                {t.agents.map(a => (
                  <Badge key={a} variant="secondary" className="text-[9px] font-mono py-0 h-4 bg-muted/40">
                    {a}
                  </Badge>
                ))}
                {t.tools.map(tool => (
                  <Badge key={tool} variant="outline" className="text-[9px] font-mono py-0 h-4 border-muted-foreground/20">
                    {tool}
                  </Badge>
                ))}
              </div>
              
              <div className="flex items-center justify-between text-[10px] text-muted-foreground font-medium pt-2">
                <div className="flex items-center gap-1.5">
                  <Bot className="h-3 w-3" />
                  {t.complexity} Complexity
                </div>
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className="h-3 w-3" />
                  HITL: {t.hitl}
                </div>
              </div>
            </CardContent>

            <CardFooter className="pt-4 border-t bg-muted/5">
              <Button 
                variant={t.installed ? "outline" : "default"} 
                className={`w-full text-xs font-bold h-9 ${!t.installed && 'shadow-lg shadow-primary/10'}`}
              >
                {t.installed ? "Configure Settings" : "Install Template"}
                <ChevronRight className="ml-2 h-3 w-3" />
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>

      {/* ── Empty State Mock ────────────────────────────────────────────────── */}
      {filteredTemplates.length === 0 && (
        <div className="py-20 text-center space-y-4 border rounded-2xl border-dashed bg-muted/10">
          <div className="h-12 w-12 rounded-full bg-muted mx-auto flex items-center justify-center">
            <Filter className="h-6 w-6 text-muted-foreground" />
          </div>
          <p className="text-muted-foreground">No templates found in this category.</p>
          <Button variant="link" onClick={() => setActiveTab("all")}>Clear filters</Button>
        </div>
      )}
    </div>
  );
}
