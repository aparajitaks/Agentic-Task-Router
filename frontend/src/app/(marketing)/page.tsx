/**
 * frontend/src/app/(marketing)/page.tsx
 *
 * WHY IT EXISTS:
 * This is the high-conversion landing page for the SaaS product.
 * It transforms the "Agentic Task Router" from an internal tool into
 * a consumer-facing AI automation product.
 *
 * WHAT IT DOES:
 * - Renders a premium Hero section with glassmorphism.
 * - Explains the core "Connect -> Automate -> Approve" workflow.
 * - Showcases features like HITL, Agent Orchestration, and Tool Calling.
 * - Provides CTA buttons for signup and demo mode.
 *
 * DESIGN PHILOSOPHY:
 * - Dark mode by default.
 * - High-contrast typography.
 * - Subtle gradients and motion (via Tailwind).
 * - Enterprise-grade SaaS aesthetic (inspired by Linear/Vercel).
 */

import Link from "next/link";
import { 
  ArrowRight, 
  ShieldCheck, 
  Zap, 
  Mail, 
  Bot, 
  Wrench, 
  CheckCircle2, 
  LayoutDashboard,
  ExternalLink
} from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground selection:bg-primary/30">
      {/* ── Navigation ────────────────────────────────────────────────────────── */}
      <header className="fixed top-0 w-full z-50 border-b bg-background/80 backdrop-blur-md">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-xl">
            <div className="h-8 w-8 rounded bg-primary flex items-center justify-center text-primary-foreground text-sm">A</div>
            <span>Antigravity</span>
          </div>
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
            <Link href="#features" className="hover:text-foreground transition-colors">Features</Link>
            <Link href="#workflow" className="hover:text-foreground transition-colors">Workflow</Link>
            <Link href="#pricing" className="hover:text-foreground transition-colors">Pricing</Link>
          </nav>
          <div className="flex items-center gap-4">
            <Link 
              href="/auth/login" 
              className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}
            >
              Log in
            </Link>
            <Link 
              href="/auth/signup" 
              className={cn(buttonVariants({ size: "sm" }), "bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg shadow-primary/20")}
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-grow pt-32 pb-20">
        {/* ── Hero Section ────────────────────────────────────────────────────── */}
        <section className="container mx-auto px-4 text-center space-y-8 max-w-4xl">
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-1000">
            <Badge variant="outline" className="py-1 px-4 mb-6 border-primary/20 bg-primary/5 text-primary">
              The Next Evolution of AI Automations
            </Badge>
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight leading-[1.1]">
              Automate your Inbox with <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-blue-400 to-emerald-400">
                Agentic Intelligence
              </span>
            </h1>
            <p className="mt-6 text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Connect your Gmail. Let autonomous AI agents classify, summarize, and draft replies. 
              Stay in control with Human-in-the-Loop approvals.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-in fade-in slide-in-from-bottom-6 duration-1000 delay-300">
            <Link 
              href="/auth/signup" 
              className={cn(buttonVariants({ size: "lg" }), "h-12 px-8 text-lg font-semibold rounded-full group")}
            >
              Deploy Your Agent
              <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link 
              href="/dashboard" 
              className={cn(buttonVariants({ size: "lg", variant: "outline" }), "h-12 px-8 text-lg font-semibold rounded-full border-muted-foreground/20")}
            >
              Explore Demo Mode
            </Link>
          </div>

          {/* Social Proof / Trusted By */}
          <div className="pt-12 animate-in fade-in duration-1000 delay-500">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/60 mb-6">
              Powered by Enterprise Grade Infrastructure
            </p>
            <div className="flex flex-wrap justify-center items-center gap-8 grayscale opacity-50 contrast-125">
              <span className="font-bold text-lg italic">LangGraph</span>
              <span className="font-bold text-lg tracking-tighter">FastAPI</span>
              <span className="font-bold text-lg">Next.js</span>
              <span className="font-bold text-lg tracking-widest underline decoration-2 decoration-primary underline-offset-4">CELERY</span>
              <span className="font-bold text-lg">PostgreSQL</span>
            </div>
          </div>
        </section>

        {/* ── Visual Demo Section ────────────────────────────────────────────── */}
        <section id="workflow" className="container mx-auto px-4 mt-32">
          <div className="relative rounded-2xl border bg-muted/30 p-2 shadow-2xl overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-tr from-primary/10 via-transparent to-emerald-400/10 opacity-50" />
            <div className="relative rounded-xl border bg-background overflow-hidden aspect-video flex items-center justify-center">
              {/* Simulated UI Preview */}
              <div className="w-full h-full flex flex-col items-center justify-center p-8 text-center space-y-4">
                <div className="p-4 rounded-full bg-primary/10 mb-4 animate-pulse">
                  <Workflow className="h-12 w-12 text-primary" />
                </div>
                <h3 className="text-2xl font-bold">Interactive Workflow Orchestration</h3>
                <p className="text-muted-foreground max-w-md">
                  Visualize agentic loops in real-time. Watch as Router Agents dispatch tasks to 
                  Summarizers, Reply Generators, and Web Search tools.
                </p>
                <div className="flex gap-2">
                  <div className="h-2 w-12 rounded-full bg-primary/20" />
                  <div className="h-2 w-24 rounded-full bg-primary" />
                  <div className="h-2 w-16 rounded-full bg-primary/20" />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Features Grid ───────────────────────────────────────────────────── */}
        <section id="features" className="container mx-auto px-4 mt-40 space-y-20">
          <div className="text-center space-y-4">
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight">Everything you need to automate.</h2>
            <p className="text-muted-foreground text-lg">Pro-grade tools for modern AI workflow management.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Bot,
                title: "Agent Orchestration",
                desc: "Multi-agent systems powered by LangGraph. Each agent specializes in a domain for maximum accuracy."
              },
              {
                icon: ShieldCheck,
                title: "Human-in-the-Loop",
                desc: "Never send an AI email without approval. Use the HITL inbox to review, edit, and resume workflows."
              },
              {
                icon: Wrench,
                title: "Dynamic Tool Calling",
                desc: "Agents can search the web, query databases, and call APIs to solve complex user requests."
              },
              {
                icon: Mail,
                title: "Gmail Integration",
                desc: "Connect your inbox in one click. Automated sync keeps your AI assistants up to date."
              },
              {
                icon: Zap,
                title: "Async Processing",
                desc: "Powered by Redis and Celery. Handle thousands of workflows concurrently without lag."
              },
              {
                icon: LayoutDashboard,
                title: "Visual Traceability",
                desc: "Every tool call, agent decision, and log is persisted and visualized for full observability."
              }
            ].map((feature, i) => (
              <Card key={i} className="border-muted/60 hover:border-primary/50 transition-all duration-300 bg-muted/10">
                <CardHeader>
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                    <feature.icon className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                  <CardDescription className="text-base text-muted-foreground leading-relaxed">
                    {feature.desc}
                  </CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </section>

        {/* ── Workflow Showcase ───────────────────────────────────────────────── */}
        <section className="mt-40 bg-muted/30 border-y py-24 overflow-hidden">
          <div className="container mx-auto px-4 flex flex-col md:flex-row items-center gap-16">
            <div className="flex-1 space-y-6">
              <Badge className="bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border-emerald-500/20">
                Productive by Design
              </Badge>
              <h2 className="text-4xl font-bold leading-tight">
                Turn your inbox into a <br />
                self-running engine.
              </h2>
              <div className="space-y-4">
                {[
                  "Summarize 50+ emails into a single morning briefing.",
                  "Auto-categorize inquiries by sentiment and urgency.",
                  "Draft professional replies based on your past writing style.",
                  "Extract action items directly into your task manager."
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                    <span className="text-muted-foreground">{item}</span>
                  </div>
                ))}
              </div>
              <Button size="lg" className="mt-4 shadow-xl shadow-primary/20">
                Get Started for Free
              </Button>
            </div>
            <div className="flex-1 relative">
              <div className="absolute -inset-4 bg-primary/20 blur-3xl rounded-full opacity-30" />
              <div className="relative rounded-2xl border bg-background p-6 shadow-xl space-y-4">
                <div className="flex items-center justify-between border-b pb-4">
                  <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-full bg-muted animate-pulse" />
                    <div className="h-3 w-24 rounded bg-muted animate-pulse" />
                  </div>
                  <Badge variant="outline" className="text-amber-400 border-amber-400/30">Awaiting Approval</Badge>
                </div>
                <div className="space-y-2">
                  <div className="h-2 w-full rounded bg-muted animate-pulse" />
                  <div className="h-2 w-5/6 rounded bg-muted animate-pulse" />
                  <div className="h-2 w-4/6 rounded bg-muted animate-pulse" />
                </div>
                <div className="flex gap-2 pt-4">
                  <div className="h-8 flex-1 rounded bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-[10px] font-bold text-emerald-400 uppercase tracking-tighter">Approve</div>
                  <div className="h-8 flex-1 rounded bg-muted flex items-center justify-center text-[10px] font-bold text-muted-foreground uppercase tracking-tighter">Edit</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── CTA Section ─────────────────────────────────────────────────────── */}
        <section className="container mx-auto px-4 mt-40">
          <div className="rounded-3xl bg-primary px-8 py-16 text-center text-primary-foreground space-y-8 relative overflow-hidden shadow-2xl shadow-primary/40">
            <div className="absolute top-0 right-0 p-12 opacity-10 rotate-12">
              <Bot className="h-64 w-64" />
            </div>
            <h2 className="text-4xl md:text-6xl font-bold tracking-tight relative z-10">
              Ready to meet your AI assistant?
            </h2>
            <p className="text-primary-foreground/80 text-xl max-w-2xl mx-auto relative z-10 leading-relaxed">
              Join 1,000+ users automating their workflows with Antigravity. 
              Start for free today. No credit card required.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 relative z-10 pt-4">
              <Button size="lg" variant="secondary" className="h-12 px-10 text-lg font-bold shadow-lg shadow-black/10">
                Get Started Now
              </Button>
              <Button size="lg" variant="ghost" className="h-12 px-10 text-lg font-bold text-primary-foreground hover:bg-white/10">
                Contact Sales
              </Button>
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ──────────────────────────────────────────────────────────── */}
      <footer className="border-t bg-muted/20 py-20 mt-20">
        <div className="container mx-auto px-4 grid md:grid-cols-4 gap-12">
          <div className="space-y-4">
            <div className="flex items-center gap-2 font-bold text-xl">
              <div className="h-8 w-8 rounded bg-primary flex items-center justify-center text-primary-foreground text-sm">A</div>
              <span>Antigravity</span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Enterprise-grade AI orchestration for modern teams. 
              Built for speed, control, and intelligence.
            </p>
          </div>
          <div className="space-y-4">
            <h4 className="font-bold">Product</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link href="#features" className="hover:text-foreground">Features</Link></li>
              <li><Link href="/dashboard" className="hover:text-foreground">Demo Mode</Link></li>
              <li><Link href="/dashboard/approvals" className="hover:text-foreground">HITL Workflow</Link></li>
              <li><Link href="/dashboard/settings" className="hover:text-foreground">Integrations</Link></li>
            </ul>
          </div>
          <div className="space-y-4">
            <h4 className="font-bold">Company</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link href="#" className="hover:text-foreground">About</Link></li>
              <li><Link href="#" className="hover:text-foreground">Blog</Link></li>
              <li><Link href="#" className="hover:text-foreground">Careers</Link></li>
              <li><Link href="#" className="hover:text-foreground">Security</Link></li>
            </ul>
          </div>
          <div className="space-y-4">
            <h4 className="font-bold">Connect</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link href="#" className="hover:text-foreground flex items-center gap-2">Twitter <ExternalLink className="h-3 w-3" /></Link></li>
              <li><Link href="#" className="hover:text-foreground flex items-center gap-2">GitHub <ExternalLink className="h-3 w-3" /></Link></li>
              <li><Link href="#" className="hover:text-foreground flex items-center gap-2">Discord <ExternalLink className="h-3 w-3" /></Link></li>
            </ul>
          </div>
        </div>
        <div className="container mx-auto px-4 mt-20 pt-8 border-t flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-muted-foreground">
          <p>© 2026 Antigravity AI Inc. All rights reserved.</p>
          <div className="flex gap-8">
            <Link href="#" className="hover:text-foreground">Privacy Policy</Link>
            <Link href="#" className="hover:text-foreground">Terms of Service</Link>
            <Link href="#" className="hover:text-foreground">Cookie Policy</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

function Workflow(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="8" height="8" x="3" y="3" rx="2" />
      <path d="M7 11v4a2 2 0 0 0 2 2h4" />
      <rect width="8" height="8" x="13" y="13" rx="2" />
    </svg>
  );
}

function Card({ children, className }: any) {
  return (
    <div className={`rounded-xl border bg-card text-card-foreground shadow ${className}`}>
      {children}
    </div>
  );
}

function CardHeader({ children, className }: any) {
  return (
    <div className={`flex flex-col space-y-1.5 p-6 ${className}`}>
      {children}
    </div>
  );
}

function CardTitle({ children, className }: any) {
  return (
    <div className={`text-2xl font-semibold leading-none tracking-tight ${className}`}>
      {children}
    </div>
  );
}

function CardDescription({ children, className }: any) {
  return (
    <div className={`text-sm text-muted-foreground ${className}`}>
      {children}
    </div>
  );
}
