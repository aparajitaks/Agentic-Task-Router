/**
 * frontend/src/app/auth/login/page.tsx
 *
 * WHY IT EXISTS:
 * Placeholder for the Clerk login integration.
 */

"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Welcome Back</CardTitle>
          <CardDescription>Login to your Antigravity account</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button className="w-full" onClick={() => window.location.href = "/dashboard"}>
            Login with Clerk (Demo)
          </Button>
          <p className="text-center text-sm text-muted-foreground">
            Don't have an account? <Link href="/auth/signup" className="text-primary hover:underline">Sign up</Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
