"use client";

/**
 * frontend/src/components/providers.tsx
 *
 * WHY IT EXISTS:
 * Client-side contexts (like React Query and Tooltips) require a "use client"
 * directive. We wrap our Next.js app in this component so the rest of the app
 * can remain Server Components by default.
 *
 * WHAT IT DOES:
 * Initializes the `QueryClient` for caching API requests.
 * Wraps the application in `TooltipProvider` for shadcn UI tooltips.
 *
 * HOW IT CONNECTS TO BACKEND:
 * React Query manages all asynchronous communication (fetching, mutating, caching)
 * with the FastAPI backend.
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { TooltipProvider } from "@/components/ui/tooltip";

export function Providers({ children }: { children: React.ReactNode }) {
  // Ensure we don't share the QueryClient across requests during SSR
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 1000, // Data is fresh for 5 seconds
            retry: 1, // Only retry once by default
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider delay={300}>{children}</TooltipProvider>
    </QueryClientProvider>
  );
}
