/**
 * frontend/src/app/(dashboard)/settings/page.tsx
 *
 * WHY IT EXISTS:
 * This is the control center for the user's personal AI behavior.
 * A real SaaS product must allow users to toggle automations and
 * manage their external integrations (Gmail).
 *
 * WHAT IT DOES:
 * - Managed Gmail connection (Connect/Disconnect/Status).
 * - Global AI preference toggles (Auto-summarize, Always-HITL).
 * - Notification preferences.
 * - Profile management.
 */

"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api-client";
import { 
  User, 
  Mail, 
  Bell, 
  ShieldCheck, 
  Zap, 
  ExternalLink, 
  Trash2, 
  Save,
  CheckCircle2,
  Lock,
  RefreshCw
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { useAuthStore } from "@/store/use-auth-store";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const [isSaving, setIsSaving] = useState(false);
  const { isGmailConnected, setGmailConnected } = useAuthStore();
  const [isDisconnecting, setIsDisconnecting] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await apiClient.get<any, any>("/gmail/status");
        setGmailConnected(res.connected);
      } catch (err) {
        console.error("Failed to fetch Gmail status", err);
      }
    };
    fetchStatus();
  }, [setGmailConnected]);

  const handleDisconnect = async () => {
    setIsDisconnecting(true);
    try {
      await apiClient.post("/gmail/disconnect");
      setGmailConnected(false);
    } catch (err) {
      console.error("Failed to disconnect Gmail", err);
    } finally {
      setIsDisconnecting(false);
    }
  };

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => setIsSaving(false), 1000);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="space-y-1">
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">Manage your account, integrations, and AI preferences.</p>
      </div>

      <Tabs defaultValue="account" className="space-y-6">
        <TabsList className="bg-muted/20 border-muted/60">
          <TabsTrigger value="account" className="gap-2">
            <User className="h-4 w-4" /> Account
          </TabsTrigger>
          <TabsTrigger value="integrations" className="gap-2">
            <Mail className="h-4 w-4" /> Integrations
          </TabsTrigger>
          <TabsTrigger value="automation" className="gap-2">
            <Zap className="h-4 w-4" /> Automation
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-2">
            <Lock className="h-4 w-4" /> Security
          </TabsTrigger>
        </TabsList>

        {/* ── Account Settings ────────────────────────────────────────────── */}
        <TabsContent value="account" className="space-y-6">
          <Card className="border-muted/60">
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>Update your personal details and how we should address you.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="full_name">Full Name</Label>
                  <Input id="full_name" defaultValue="Aparajit Aks" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input id="email" defaultValue="user@example.com" disabled />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-muted/60">
            <CardHeader>
              <CardTitle>Regional & Language</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Timezone</Label>
                  <Input defaultValue="UTC (Coordinated Universal Time)" />
                </div>
                <div className="space-y-2">
                  <Label>Primary Language</Label>
                  <Input defaultValue="English (US)" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Integrations Settings ────────────────────────────────────────── */}
        <TabsContent value="integrations" className="space-y-6">
          <Card className="border-muted/60">
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="space-y-1">
                <CardTitle>Connected Platforms</CardTitle>
                <CardDescription>Authorize Antigravity to work across your digital workspace.</CardDescription>
              </div>
              <Badge variant="outline" className="text-primary border-primary/20 bg-primary/5">1/4 Connected</Badge>
            </CardHeader>
            <CardContent className="space-y-6">
              
              {/* Gmail Connection Row */}
              <div className={cn(
                "flex items-center justify-between p-4 rounded-xl border transition-all",
                isGmailConnected ? "bg-emerald-500/5 border-emerald-500/20" : "bg-muted/10 border-muted"
              )}>
                <div className="flex items-center gap-4">
                  <div className={cn(
                    "h-12 w-12 rounded flex items-center justify-center border shadow-sm",
                    isGmailConnected ? "bg-white" : "bg-muted grayscale"
                  )}>
                    <Mail className={cn("h-6 w-6", isGmailConnected ? "text-red-500" : "text-muted-foreground")} />
                  </div>
                  <div>
                    <p className="font-bold">Google Workspace / Gmail</p>
                    <p className="text-xs text-muted-foreground">
                      {isGmailConnected ? "Connected and syncing." : "Not connected. Required for email orchestration."}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {isGmailConnected ? (
                    <>
                      <Button variant="outline" size="sm" className="h-8 text-xs border-muted-foreground/20">
                        Sync Status
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-8 text-xs text-red-400 hover:bg-red-500/10 hover:text-red-500"
                        onClick={handleDisconnect}
                        disabled={isDisconnecting}
                      >
                        {isDisconnecting ? "Disconnecting..." : "Disconnect"}
                      </Button>
                    </>
                  ) : (
                    <Button 
                      size="sm" 
                      className="h-8 text-xs gap-2"
                      onClick={async () => {
                        try {
                          const res: any = await apiClient.get("/gmail/connect");
                          if (res.auth_url) window.location.href = res.auth_url;
                        } catch (err) {
                          console.error("Failed to connect", err);
                        }
                      }}
                    >
                      Connect Gmail <ExternalLink className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              </div>

              {/* Slack Placeholder */}
              <div className="flex items-center justify-between p-4 rounded-xl border border-dashed bg-muted/5 opacity-60">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded bg-white flex items-center justify-center border shadow-sm grayscale">
                    <Zap className="h-6 w-6 text-purple-500" />
                  </div>
                  <div>
                    <p className="font-bold">Slack</p>
                    <p className="text-xs text-muted-foreground">Post workflow alerts to channels.</p>
                  </div>
                </div>
                <Button variant="outline" size="sm" className="h-8 text-xs gap-2">
                  Connect <ExternalLink className="h-3 w-3" />
                </Button>
              </div>

            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Automation Settings ─────────────────────────────────────────── */}
        <TabsContent value="automation" className="space-y-6">
          <Card className="border-muted/60">
            <CardHeader>
              <CardTitle>Global AI Preferences</CardTitle>
              <CardDescription>Define how much autonomy you want to grant your agents.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-base">Universal Approval Gate (HITL)</Label>
                  <p className="text-sm text-muted-foreground">Always ask for permission before sending external emails.</p>
                </div>
                <Switch defaultChecked />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-base">Auto-Summarization</Label>
                  <p className="text-sm text-muted-foreground">Summarize non-critical emails automatically at 9:00 AM.</p>
                </div>
                <Switch defaultChecked />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-base">Aggressive Task Extraction</Label>
                  <p className="text-sm text-muted-foreground">Allow AI to create tasks from your emails without confirmation.</p>
                </div>
                <Switch />
              </div>

            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Security Settings ───────────────────────────────────────────── */}
        <TabsContent value="security" className="space-y-6">
          <Card className="border-muted/60 border-red-500/20 bg-red-500/5">
            <CardHeader>
              <CardTitle className="text-red-500">Danger Zone</CardTitle>
              <CardDescription>Permanent actions that cannot be undone.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-bold">Delete Account</p>
                  <p className="text-xs text-muted-foreground">Permanently delete your profile and all associated AI logs.</p>
                </div>
                <Button variant="destructive" size="sm" className="gap-2">
                  <Trash2 className="h-3.5 w-3.5" />
                  Delete Everything
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* ── Sticky Footer Actions ─────────────────────────────────────────── */}
      <div className="flex justify-end gap-3 pt-6 border-t">
        <Button variant="ghost">Cancel</Button>
        <Button onClick={handleSave} disabled={isSaving} className="gap-2 min-w-[120px]">
          {isSaving ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <>
              <Save className="h-4 w-4" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
