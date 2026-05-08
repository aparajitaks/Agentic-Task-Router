/**
 * frontend/src/app/dashboard/layout.tsx
 *
 * WHY IT EXISTS:
 * Next.js route groups (the parenthesis syntax) allow us to apply a shared UI layout
 * without adding a path segment to the URL.
 *
 * WHAT IT DOES:
 * Wraps all dashboard pages with the Sidebar and Header. Controls the dynamic
 * padding when the sidebar expands or collapses.
 *
 * HOW IT CONNECTS TO BACKEND:
 * N/A - Pure UI layout logic.
 */

"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { useUiStore } from "@/store/use-ui-store";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isSidebarOpen } = useUiStore();

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Fixed Sidebar */}
      <Sidebar />
      
      {/* Main Content wrapper */}
      <div 
        className={`flex flex-col flex-1 transition-all duration-300 ease-in-out ${
          isSidebarOpen ? "md:pl-64" : "md:pl-16"
        }`}
      >
        <Header />
        
        {/* Scrollable Page Content */}
        <main className="flex-1 overflow-y-auto p-6 relative">
          <div className="mx-auto max-w-7xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
