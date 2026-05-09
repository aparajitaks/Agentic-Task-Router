/**
 * frontend/src/components/dashboard/onboarding-overlay.tsx
 * 
 * WHY IT EXISTS:
 * To provide a high-end, immersive onboarding experience for new users.
 * This prevents them from seeing a broken/empty dashboard and guides
 * them through the critical "Connect Gmail" step.
 */

"use client";

import { useState } from "react";
import { 
  Mail, 
  Sparkles, 
  ShieldCheck, 
  Zap, 
  ArrowRight,
  Loader2,
  CheckCircle2,
  ExternalLink
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";
import { useAuthStore } from "@/store/use-auth-store";

export function OnboardingOverlay() {
  const { setDemoMode } = useAuthStore();
  const [isConnecting, setIsConnecting] = useState(false);

  const handleConnectGmail = async () => {
    setIsConnecting(true);
    try {
      // Fetch the auth URL from our backend
      const res: any = await apiClient.get("/gmail/connect");
      if (res.auth_url) {
        // Redirect to Google
        window.location.href = res.auth_url;
      }
    } catch (error) {
      console.error("Failed to get auth URL", error);
      setIsConnecting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/95 backdrop-blur-md animate-in fade-in duration-500">
      <div className="max-w-4xl w-full px-4 grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        
        {/* Left Side: Value Prop */}
        <div className="space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-bold uppercase tracking-wider">
            <Sparkles className="h-3 w-3" />
            Next-Gen AI Orchestration
          </div>
          
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight">
            Welcome to the <span className="text-primary">Future</span> of Inbox Productivity.
          </h1>
          
          <p className="text-lg text-muted-foreground leading-relaxed">
            Connect your Gmail to deploy autonomous AI agents that categorize, summarize, and draft replies while you focus on deep work.
          </p>

          <div className="space-y-4 pt-4">
            <div className="flex items-start gap-4">
              <div className="h-6 w-6 rounded-full bg-emerald-500/10 flex items-center justify-center shrink-0 mt-1">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              </div>
              <p className="text-sm">Real-time email ingestion & prioritization.</p>
            </div>
            <div className="flex items-start gap-4">
              <div className="h-6 w-6 rounded-full bg-emerald-500/10 flex items-center justify-center shrink-0 mt-1">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              </div>
              <p className="text-sm">Human-in-the-loop approval workflows.</p>
            </div>
            <div className="flex items-start gap-4">
              <div className="h-6 w-6 rounded-full bg-emerald-500/10 flex items-center justify-center shrink-0 mt-1">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              </div>
              <p className="text-sm">Secure OAuth2 integration (Read/Modify only).</p>
            </div>
          </div>
        </div>

        {/* Right Side: CTA Card */}
        <Card className="border-primary/20 shadow-2xl shadow-primary/10 overflow-hidden bg-gradient-to-b from-background to-muted/50">
          <CardContent className="p-8 space-y-8">
            <div className="h-20 w-20 rounded-2xl bg-primary flex items-center justify-center mx-auto shadow-lg shadow-primary/20 rotate-3">
              <Mail className="h-10 w-10 text-primary-foreground" />
            </div>

            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold">Connect your Workspace</h2>
              <p className="text-sm text-muted-foreground px-4">
                Grant access to your Gmail to start training your agents. We never share your data.
              </p>
            </div>

            <div className="space-y-3">
              <Button 
                onClick={handleConnectGmail}
                disabled={isConnecting}
                className="w-full h-12 text-lg font-bold gap-2 shadow-lg shadow-primary/20 group"
              >
                {isConnecting ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <>
                    Connect with Gmail
                    <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </Button>
              
              <Button 
                variant="ghost" 
                className="w-full h-10 text-xs text-muted-foreground gap-2"
                onClick={() => setDemoMode(true)}
              >
                <Zap className="h-3.5 w-3.5 text-amber-500" />
                Explore Demo Workspace
              </Button>
            </div>

            <div className="pt-4 flex items-center justify-center gap-6 opacity-40 grayscale pointer-events-none">
              <ShieldCheck className="h-6 w-6" />
              <Zap className="h-6 w-6" />
              <ExternalLink className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
