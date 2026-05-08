/**
 * frontend/src/app/auth/signup/page.tsx
 *
 * WHY IT EXISTS:
 * Placeholder for the Clerk signup integration.
 */

"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function SignupPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Create Account</CardTitle>
          <CardDescription>Start your AI automation journey</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button className="w-full" onClick={() => window.location.href = "/onboarding"}>
            Sign up with Clerk (Demo)
          </Button>
          <p className="text-center text-sm text-muted-foreground">
            Already have an account? <Link href="/auth/login" className="text-primary hover:underline">Log in</Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
