/**
 * frontend/src/app/(dashboard)/loading.tsx
 *
 * WHY IT EXISTS:
 * Next.js automatically wraps page components in React Suspense. This file provides
 * the fallback UI while the page chunks or async data are loading.
 *
 * WHAT IT DOES:
 * Displays a clean, generic skeleton loader matching the dashboard aesthetic.
 *
 * HOW IT CONNECTS TO BACKEND:
 * Masks the latency of initial API requests to FastAPI.
 */

import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardLoading() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96" />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-32 w-full rounded-xl" />
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-7">
        <Skeleton className="h-[400px] col-span-4 rounded-xl" />
        <Skeleton className="h-[400px] col-span-3 rounded-xl" />
      </div>
    </div>
  );
}
