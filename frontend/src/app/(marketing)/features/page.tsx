/**
 * frontend/src/app/(marketing)/features/page.tsx
 */

import Link from "next/link";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function FeaturesPage() {
  return (
    <div className="container mx-auto px-4 py-32 text-center space-y-8">
      <h1 className="text-5xl font-bold">Powerful AI Features</h1>
      <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
        Antigravity brings enterprise-grade agentic loops to your everyday workflows.
      </p>
      <Link 
        href="/" 
        className={cn(buttonVariants({ variant: "default" }))}
      >
        Back to Home
      </Link>
    </div>
  );
}
