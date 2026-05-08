/**
 * frontend/src/components/layout/sidebar.tsx
 *
 * WHY IT EXISTS:
 * Primary navigation element for the dashboard. It needs to be collapsible to
 * maximize screen real estate when viewing complex DAG workflows.
 *
 * WHAT IT DOES:
 * Renders navigation links using Lucide icons. Uses Zustand `useUiStore` to
 * animate width transitions.
 *
 * HOW IT CONNECTS TO BACKEND:
 * N/A - Pure UI component.
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  Workflow, 
  Mail, 
  Bot, 
  Wrench, 
  TerminalSquare, 
  Settings,
  ChevronLeft
} from "lucide-react";
import { useUiStore } from "@/store/use-ui-store";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const NAV_ITEMS = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Workflows", href: "/workflows", icon: Workflow },
  { name: "Emails", href: "/emails", icon: Mail },
  { name: "Agents", href: "/agents", icon: Bot },
  { name: "Tools", href: "/tools", icon: Wrench },
  { name: "Logs", href: "/logs", icon: TerminalSquare },
];

export function Sidebar() {
  const pathname = usePathname();
  const { isSidebarOpen, toggleSidebar } = useUiStore();

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-50 flex flex-col border-r bg-background/80 backdrop-blur-md transition-all duration-300 ease-in-out",
        isSidebarOpen ? "w-64" : "w-16"
      )}
    >
      {/* Logo Area */}
      <div className="flex h-16 items-center justify-between px-4 border-b">
        <div className={cn("flex items-center gap-2 font-bold transition-opacity duration-300", 
          !isSidebarOpen && "opacity-0 invisible w-0"
        )}>
          <div className="h-6 w-6 rounded bg-primary flex items-center justify-center text-primary-foreground text-xs">A</div>
          <span>Antigravity</span>
        </div>
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={toggleSidebar}
          className="h-8 w-8 ml-auto"
        >
          <ChevronLeft className={cn("h-4 w-4 transition-transform duration-300", !isSidebarOpen && "rotate-180")} />
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-2">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors relative group",
                isActive 
                  ? "bg-primary/10 text-primary" 
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              <span className={cn("transition-opacity duration-300 whitespace-nowrap", !isSidebarOpen && "opacity-0 invisible w-0")}>
                {item.name}
              </span>
              
              {/* Tooltip for collapsed state */}
              {!isSidebarOpen && (
                <div className="absolute left-14 rounded-md bg-popover px-2 py-1 text-xs font-medium text-popover-foreground opacity-0 shadow-md group-hover:opacity-100 transition-opacity pointer-events-none">
                  {item.name}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer Settings */}
      <div className="p-2 border-t">
        <Link
          href="/settings"
          className={cn(
            "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors group",
          )}
        >
          <Settings className="h-5 w-5 shrink-0" />
          <span className={cn("transition-opacity duration-300", !isSidebarOpen && "opacity-0 invisible w-0")}>
            Settings
          </span>
        </Link>
      </div>
    </aside>
  );
}
