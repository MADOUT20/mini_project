"use client"
// Landing page entry point for the public-facing frontend experience.

import Link from "next/link"
import {
  Shield,
  Activity,
  Search,
  ShieldAlert,
  Globe,
  Server,
  ArrowRight,
  CheckCircle2,
  Zap,
  Lock,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { ThemeToggle } from "@/components/theme-toggle"
import { Footer } from "@/components/footer"

const features = [
  {
    icon: Activity,
    title: "Packet Capture",
    description:
      "Real-time monitoring of all incoming and outgoing network traffic with source/destination IP logging.",
  },
  {
    icon: Search,
    title: "Deep Packet Inspection",
    description:
      "Comprehensive analysis of packet headers and payloads to identify malicious code hidden within traffic.",
  },
  {
    icon: ShieldAlert,
    title: "Threat Detection",
    description:
      "Three-pronged approach using signature-based, heuristic-based, and behavior-based detection methods.",
  },
  {
    icon: Globe,
    title: "Traffic Analysis",
    description:
      "Foreign vs local traffic classification using IP geolocation with enhanced monitoring for external connections.",
  },
  {
    icon: Zap,
    title: "Automated Response",
    description:
      "Multi-stage response pipeline with instant alerts, forensic logging, and optional automatic IP blocking.",
  },
  {
    icon: Server,
    title: "OS Protection",
    description:
      "Multi-layer defense preventing malicious payloads from reaching critical applications and maintaining system integrity.",
  },
]

const stats = [
  { value: "3", label: "Detection Methods" },
  { value: "24/7", label: "Real-Time Monitoring" },
  { value: "100%", label: "Network Coverage" },
]

export default function LandingPage() {
  return (
    <>
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
              <Shield className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-lg font-bold text-foreground">NetGuard</span>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link href="/login">
              <Button variant="ghost" size="sm">Sign In</Button>
            </Link>
            <Link href="/signup">
              <Button size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 opacity-[0.03]">
          <div className="absolute top-0 left-0 w-full h-full" style={{
            backgroundImage: `radial-gradient(circle, hsl(var(--primary)) 1px, transparent 1px)`,
            backgroundSize: '40px 40px'
          }} />
        </div>
        <div className="relative mx-auto max-w-6xl px-6 py-24 lg:py-32">
          <div className="mx-auto max-w-3xl text-center space-y-8">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm text-primary">
              <Lock className="h-3.5 w-3.5" />
              Network Security Solution
            </div>
            <h1 className="text-4xl font-bold tracking-tight text-balance text-foreground sm:text-5xl lg:text-6xl">
              Network-Level Malware Detection System
            </h1>
            <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl mx-auto">
              A comprehensive approach to real-time threat detection and operating system protection. Monitor, analyze, and defend your network infrastructure with advanced packet inspection.
            </p>
            <div className="flex items-center justify-center gap-4 flex-wrap">
              <Link href="/dashboard">
                <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 h-12 px-8">
                  Open Dashboard
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <Link href="/signup">
                <Button size="lg" variant="outline" className="h-12 px-8">
                  Create Account
                </Button>
              </Link>
            </div>
          </div>

          {/* Stats */}
          <div className="mt-20 grid grid-cols-3 gap-8 mx-auto max-w-xl">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl font-bold text-primary">{stat.value}</div>
                <div className="mt-1 text-sm text-muted-foreground">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-border bg-card">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mx-auto max-w-2xl text-center space-y-4 mb-16">
            <h2 className="text-3xl font-bold text-foreground">Core System Modules</h2>
            <p className="text-muted-foreground leading-relaxed">
              Each module works in concert to provide comprehensive network security through real-time monitoring and intelligent threat detection.
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <Card key={feature.title} className="bg-background border-border hover:border-primary/30 transition-colors">
                <CardContent className="p-6 space-y-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <feature.icon className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="text-base font-semibold text-foreground">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Advantages and Limitations */}
      <section className="border-t border-border">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="grid gap-12 lg:grid-cols-2">
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-foreground">Key Advantages</h2>
              <div className="space-y-4">
                {[
                  "Real-time monitoring and detection",
                  "Early threat identification reduces damage",
                  "Significantly improves network security posture",
                  "Cost-effective for educational environments",
                  "Easy to understand and implement",
                ].map((item) => (
                  <div key={item} className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0 mt-0.5" />
                    <span className="text-sm text-foreground">{item}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-foreground">Current Limitations</h2>
              <div className="space-y-4">
                {[
                  "Cannot inspect fully encrypted payloads (SSL/TLS)",
                  "Signature-based detection fails for zero-day attacks",
                  "Performance may degrade with heavy traffic loads",
                  "Requires regular signature database updates",
                ].map((item) => (
                  <div key={item} className="flex items-start gap-3">
                    <div className="h-5 w-5 flex items-center justify-center shrink-0 mt-0.5">
                      <div className="h-1.5 w-1.5 rounded-full bg-muted-foreground" />
                    </div>
                    <span className="text-sm text-muted-foreground">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Future Enhancements */}
      <section className="border-t border-border bg-card">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="grid gap-12 lg:grid-cols-2 items-center">
            <div className="space-y-6">
              <h2 className="text-3xl font-bold text-foreground">Applications & Future</h2>
              <p className="text-muted-foreground leading-relaxed">
                Currently deployed across college and university networks, corporate LAN environments, research labs, and educational cybersecurity projects.
              </p>
              <div className="space-y-3">
                {[
                  "Machine learning integration for anomaly detection",
                  "Encrypted traffic analysis capabilities",
                  "Cloud-based threat intelligence feeds",
                  "Automatic quarantine systems",
                ].map((item) => (
                  <div key={item} className="flex items-center gap-3">
                    <ArrowRight className="h-4 w-4 text-primary shrink-0" />
                    <span className="text-sm text-foreground">{item}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Card className="bg-background border-border p-5">
                <div className="text-3xl font-bold text-primary">12K+</div>
                <div className="text-sm text-muted-foreground mt-1">Signatures Database</div>
              </Card>
              <Card className="bg-background border-border p-5">
                <div className="text-3xl font-bold text-primary">342</div>
                <div className="text-sm text-muted-foreground mt-1">Heuristic Rules</div>
              </Card>
              <Card className="bg-background border-border p-5">
                <div className="text-3xl font-bold text-primary">TCP</div>
                <div className="text-sm text-muted-foreground mt-1">UDP, ICMP Support</div>
              </Card>
              <Card className="bg-background border-border p-5">
                <div className="text-3xl font-bold text-primary">DPI</div>
                <div className="text-sm text-muted-foreground mt-1">Deep Packet Inspection</div>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-border">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <div className="mx-auto max-w-2xl text-center space-y-6">
            <h2 className="text-3xl font-bold text-foreground text-balance">
              Ready to protect your network?
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Get started with NetGuard and deploy comprehensive network-level malware detection for your campus, corporate LAN, or research environment.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link href="/dashboard">
                <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90">
                  Launch Dashboard
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
    <Footer />
    </>
  )
}
