/**
 * frontend/src/app/layout.tsx
 *
 * WHY IT EXISTS:
 * The root layout defines the HTML skeleton, global fonts, and global providers
 * for the entire Next.js application.
 *
 * WHAT IT DOES:
 * Renders the Sidebar and Header if inside the dashboard view. Loads the global
 * CSS and instantiates the client-side `Providers`.
 *
 * HOW IT CONNECTS TO BACKEND:
 * N/A - Structural frontend component.
 */

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Agentic Router Platform",
  description: "Enterprise Autonomous AI Workflow Orchestration",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} min-h-screen bg-background text-foreground antialiased selection:bg-primary/30`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
