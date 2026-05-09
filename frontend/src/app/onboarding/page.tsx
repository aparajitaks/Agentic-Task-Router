/**
 * frontend/src/app/onboarding/page.tsx
 *
 * WHY IT EXISTS:
 * First-time user experience is the make-or-break moment for SaaS.
 * This wizard guides users through connecting their Gmail and picking
 * their first AI workflow templates.
 *
 * WHAT IT DOES:
 * - Managed multi-step state (Welcome -> Connect -> Templates -> Ready).
 * - Simulated Gmail connection flow.
 * - Workflow template selection UI.
 * - Progress indicator to keep users engaged.
 */

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { 
  Check, 
  Mail, 
  Bot, 
  Sparkles, 
  ArrowRight, 
  ChevronRight,
  ShieldCheck,
  Zap,
  LayoutDashboard
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const STEPS = [
  { id: "welcome", title: "Welcome" },
  { id: "connect", title: "Connect" },
  { id: "templates", title: "Automate" },
  { id: "ready", title: "Ready" }
];

const TEMPLATES = [
  {
    id: "summarizer",
    name: "Morning Briefing",
    desc: "Summarize the last 24h of emails into a single bulleted report.",
    icon: Sparkles,
    badge: "Most Popular"
  },
  {
    id: "reply",
    name: "Smart Auto-Draft",
    desc: "Draft professional replies for incoming inquiries. Awaiting your approval.",
    icon: Mail,
    badge: "HITL Required"
  },
  {
    id: "priority",
    name: "Priority Guard",
    desc: "Flag urgent emails and escalate them to your push notifications.",
    icon: ShieldCheck,
    badge: "Critical"
  },
  {
    id: "tasks",
    name: "Task Extractor",
    desc: "Identify action items and extract them into your workspace.",
    icon: Zap,
    badge: "Productivity"
  }
];

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [selectedTemplates, setSelectedTemplates] = useState<string[]>(["summarizer"]);

  const progress = ((currentStep + 1) / STEPS.length) * 100;

  const nextStep = async () => {
    if (currentStep === 0) {
      setIsSyncing(true);
      // Sync user on first step
      try {
        await apiClient.post("/users/sync-user", {
          clerk_id: "demo_user_123",
          email: "demo@example.com",
          full_name: "Demo User"
        });
      } catch (e) {
        console.error("Failed to sync user", e);
        // We continue anyway in demo mode for UX resilience
      } finally {
        setIsSyncing(false);
      }
    }

    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      router.push("/dashboard");
    }
  };

  const toggleTemplate = (id: string) => {
    setSelectedTemplates(prev => 
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    );
  };

  const handleConnectGmail = async () => {
    setIsConnecting(true);
    try {
      const response = await apiClient.get<any, any>("/gmail/connect");
      const authUrl = response.auth_url || (response.data && response.data.auth_url);
      if (authUrl) {
        // Same-tab redirect: Google returns to /dashboard?auth_success=true
        // which the dashboard already handles to update state.
        window.location.href = authUrl;
      } else {
        console.error("No auth_url received from backend");
        setIsConnecting(false);
      }
    } catch (e) {
      console.error("Failed to get Gmail auth URL", e);
      setIsConnecting(false);
    }
  };

  return (
    <div className="min-h-screen bg-muted/30 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
        
        {/* Header & Progress */}
        <div className="space-y-4 text-center">
          <div className="flex items-center justify-center gap-2 font-bold text-2xl mb-2">
            <div className="h-8 w-8 rounded bg-primary flex items-center justify-center text-primary-foreground text-sm">A</div>
            <span>Antigravity</span>
          </div>
          <div className="flex justify-between items-center max-w-xs mx-auto mb-2">
            {STEPS.map((step, idx) => (
              <div 
                key={step.id} 
                className={`h-2 w-2 rounded-full transition-colors duration-500 ${idx <= currentStep ? 'bg-primary' : 'bg-muted-foreground/20'}`} 
              />
            ))}
          </div>
          <h2 className="text-3xl font-bold tracking-tight">{STEPS[currentStep].title}</h2>
          <Progress value={progress} className="h-1" />
        </div>

        <Card className="shadow-2xl border-muted/60">
          <CardContent className="pt-8">
            
            {/* ── Step 0: Welcome ───────────────────────────────────────────── */}
            {currentStep === 0 && (
              <div className="space-y-6 text-center py-8">
                <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                  <Bot className="h-8 w-8 text-primary" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-2xl font-bold">Your AI assistant is ready.</h3>
                  <p className="text-muted-foreground max-w-md mx-auto">
                    Let's set up your workspace. In less than 2 minutes, you'll have an 
                    autonomous agentic loop running directly in your inbox.
                  </p>
                </div>
                <Button 
                  size="lg" 
                  onClick={nextStep} 
                  disabled={isSyncing}
                  className="px-12 rounded-full group"
                >
                  {isSyncing ? "Initializing..." : "Begin Setup"}
                  {!isSyncing && <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />}
                </Button>
              </div>
            )}

            {/* ── Step 1: Connect Gmail ───────────────────────────────────────── */}
            {currentStep === 1 && (
              <div className="space-y-6">
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Step 1: Connect your Inbox</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    We need secure access to read and respond to your emails. 
                    We use restricted OAuth scopes and your data is encrypted at rest.
                  </p>
                </div>
                
                <div className="p-6 rounded-xl border border-dashed border-muted-foreground/20 bg-muted/10 space-y-4">
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded bg-white flex items-center justify-center border shadow-sm">
                      <Mail className="h-6 w-6 text-red-500" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">Google Workspace / Gmail</p>
                      <p className="text-xs text-muted-foreground">Authorize Antigravity to manage workflows</p>
                    </div>
                    <Button 
                      onClick={handleConnectGmail} 
                      disabled={isConnecting}
                      className={isConnecting ? "bg-muted" : "bg-primary"}
                    >
                      {isConnecting ? "Connecting..." : "Connect"}
                    </Button>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <ShieldCheck className="h-3 w-3 text-emerald-500" />
                  We never store your passwords. One-click disconnect at any time.
                </div>
              </div>
            )}

            {/* ── Step 2: Templates ───────────────────────────────────────────── */}
            {currentStep === 2 && (
              <div className="space-y-6">
                <div className="space-y-1">
                  <h3 className="text-xl font-semibold">Choose your Automations</h3>
                  <p className="text-sm text-muted-foreground">Select the workflows you'd like to enable immediately.</p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {TEMPLATES.map((t) => (
                    <div 
                      key={t.id}
                      onClick={() => toggleTemplate(t.id)}
                      className={`cursor-pointer p-4 rounded-xl border transition-all duration-200 text-left space-y-2 ${
                        selectedTemplates.includes(t.id) 
                          ? 'border-primary bg-primary/5 ring-1 ring-primary' 
                          : 'border-muted-foreground/20 hover:border-muted-foreground/40'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <t.icon className={`h-5 w-5 ${selectedTemplates.includes(t.id) ? 'text-primary' : 'text-muted-foreground'}`} />
                        <Badge variant="outline" className="text-[9px] px-1 py-0 h-4 border-muted-foreground/20">{t.badge}</Badge>
                      </div>
                      <p className="font-semibold text-sm">{t.name}</p>
                      <p className="text-[11px] text-muted-foreground leading-tight">{t.desc}</p>
                    </div>
                  ))}
                </div>

                <div className="pt-4">
                  <Button className="w-full rounded-full" onClick={nextStep}>
                    Enable {selectedTemplates.length} Workflows
                  </Button>
                </div>
              </div>
            )}

            {/* ── Step 3: Ready ──────────────────────────────────────────────── */}
            {currentStep === 3 && (
              <div className="space-y-8 text-center py-4">
                <div className="mx-auto relative">
                  <div className="absolute inset-0 bg-primary/20 blur-2xl rounded-full" />
                  <div className="relative h-20 w-20 bg-primary rounded-full flex items-center justify-center mx-auto text-primary-foreground shadow-xl">
                    <Check className="h-10 w-10 stroke-[3px]" />
                  </div>
                </div>
                <div className="space-y-2">
                  <h3 className="text-2xl font-bold">You're all set!</h3>
                  <p className="text-muted-foreground max-w-md mx-auto">
                    Your AI agents are now monitoring your inbox. Head to your dashboard to see 
                    the orchestration in action.
                  </p>
                </div>

                <div className="grid grid-cols-3 gap-2 py-4">
                  <div className="p-3 rounded-lg bg-muted/40 text-center space-y-1">
                    <Bot className="h-4 w-4 mx-auto text-primary" />
                    <p className="text-[10px] font-bold uppercase tracking-tighter">Agents Active</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted/40 text-center space-y-1">
                    <LayoutDashboard className="h-4 w-4 mx-auto text-primary" />
                    <p className="text-[10px] font-bold uppercase tracking-tighter">Dashboard Live</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted/40 text-center space-y-1">
                    <ShieldCheck className="h-4 w-4 mx-auto text-primary" />
                    <p className="text-[10px] font-bold uppercase tracking-tighter">HITL Guarded</p>
                  </div>
                </div>

                <Button size="lg" onClick={() => router.push("/dashboard")} className="w-full rounded-full bg-primary hover:bg-primary/90 text-primary-foreground">
                  Launch Workspace
                </Button>
              </div>
            )}

          </CardContent>
        </Card>

        {/* Footer info */}
        <p className="text-center text-xs text-muted-foreground">
          {currentStep === 1 && "By connecting, you agree to our Service Terms and Privacy Policy."}
          {currentStep === 2 && "You can customize or disable these workflows anytime in Settings."}
        </p>
      </div>
    </div>
  );
}
