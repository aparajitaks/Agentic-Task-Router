/**
 * frontend/src/components/layout/sidebar.tsx
 *
 * WHY IT EXISTS:
 * Primary navigation element for the SaaS dashboard. It needs to be collapsible
 * and reflect the user-centric product structure.
 *
 * WHAT IT DOES:
 * Renders navigation links using Lucide icons. Uses Zustand `useUiStore` to
 * animate width transitions and manages active route states.
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  Mail, 
  Bot, 
  Settings,
  ShieldCheck,
  Zap,
  FileText
} from "lucide-react";
import { useUiStore } from "@/store/use-ui-store";
import { useAuthStore } from "@/store/use-auth-store";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const NAV_ITEMS = [
  { name: "My Workspace", href: "/dashboard", icon: LayoutDashboard },
  { name: "Automations", href: "/dashboard/workflows", icon: Zap },
  { name: "Templates", href: "/dashboard/templates", icon: Bot },
  { name: "Review Queue", href: "/dashboard/approvals", icon: ShieldCheck },
  { name: "Inbox Sync", href: "/dashboard/emails", icon: Mail },
  { name: "Activity Logs", href: "/dashboard/logs", icon: FileText },
];

export function Sidebar() {
  const pathname = usePathname();
  const { isSidebarOpen, setSidebarOpen } = useUiStore();
  const { isGmailConnected } = useAuthStore();

  return (
    <aside 
      className={cn(
        "fixed left-0 top-0 z-40 h-screen border-r bg-card transition-all duration-300 ease-in-out",
        isSidebarOpen ? "w-64" : "w-16"
      )}
    >
      <div className="flex h-full flex-col">
        {/* Brand Logo Section */}
        <div className="flex h-16 items-center px-4 border-b bg-muted/30">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-primary text-primary-foreground shadow-lg shadow-primary/20">
              <span className="font-bold">A</span>
            </div>
            {isSidebarOpen && (
              <span className="font-bold text-lg tracking-tight">Antigravity</span>
            )}
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 space-y-1 p-2">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all group",
                  isActive 
                    ? "bg-primary text-primary-foreground shadow-md" 
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <item.icon className={cn("h-5 w-5 shrink-0", !isActive && "group-hover:text-primary transition-colors")} />
                {isSidebarOpen && <span>{item.name}</span>}
                {isActive && isSidebarOpen && (
                  <div className="ml-auto h-1.5 w-1.5 rounded-full bg-primary-foreground" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer: User Workspace Info / Settings / Toggle */}
        <div className="border-t p-2 space-y-1">
          {isSidebarOpen && (
            <div className={cn(
              "mb-2 px-3 py-2 rounded-lg border flex items-center justify-between transition-all",
              isGmailConnected ? "bg-emerald-500/5 border-emerald-500/10" : "bg-red-500/5 border-red-500/10"
            )}>
              <div className="flex items-center gap-2">
                <div className={cn("h-1.5 w-1.5 rounded-full animate-pulse", isGmailConnected ? "bg-emerald-500" : "bg-red-500")} />
                <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Gmail</span>
              </div>
              <span className={cn("text-[9px] font-bold uppercase", isGmailConnected ? "text-emerald-500" : "text-red-500")}>
                {isGmailConnected ? "Active" : "Required"}
              </span>
            </div>
          )}

          <Link
            href="/dashboard/settings"
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all group",
              pathname === "/dashboard/settings" 
                ? "bg-primary text-primary-foreground shadow-md" 
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <Settings className={cn("h-5 w-5 shrink-0", pathname !== "/dashboard/settings" && "group-hover:text-primary transition-colors")} />
            {isSidebarOpen && <span>Settings</span>}
          </Link>

          <Button
            variant="ghost"
            size="icon"
            className="w-full justify-start gap-3 h-10 px-3 hover:bg-muted"
            onClick={() => setSidebarOpen(!isSidebarOpen)}
          >
            <LayoutDashboard className="h-5 w-5" />
            {isSidebarOpen && <span className="text-sm">Collapse View</span>}
          </Button>
        </div>
      </div>
    </aside>
  );
}
