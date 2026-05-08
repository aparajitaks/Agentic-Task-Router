/**
 * frontend/src/components/layout/header.tsx
 *
 * WHY IT EXISTS:
 * Top navigation bar providing user context, global search, and breadcrumbs.
 *
 * WHAT IT DOES:
 * Displays dynamic page titles, notifications, and user profile mock.
 *
 * HOW IT CONNECTS TO BACKEND:
 * Will eventually connect to user settings or global search API endpoints.
 */

"use client";

import { usePathname } from "next/navigation";
import { Bell, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export function Header() {
  const pathname = usePathname();
  
  // Very basic breadcrumb derivation
  const title = pathname === "/" 
    ? "Overview" 
    : pathname.split("/")[1].charAt(0).toUpperCase() + pathname.split("/")[1].slice(1);

  return (
    <header className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-4 border-b bg-background/80 backdrop-blur-md px-6">
      <div className="flex flex-1 items-center gap-4">
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative hidden md:block">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search workflows..."
            className="w-64 rounded-full bg-muted/50 pl-9 border-none focus-visible:ring-1"
          />
        </div>
        
        <Button variant="ghost" size="icon" className="relative h-9 w-9 rounded-full">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 flex h-2 w-2 rounded-full bg-destructive" />
          <span className="sr-only">Toggle notifications</span>
        </Button>
        
        <Avatar className="h-9 w-9 border cursor-pointer hover:opacity-80 transition-opacity">
          <AvatarImage src="https://github.com/shadcn.png" alt="@shadcn" />
          <AvatarFallback>AG</AvatarFallback>
        </Avatar>
      </div>
    </header>
  );
}
