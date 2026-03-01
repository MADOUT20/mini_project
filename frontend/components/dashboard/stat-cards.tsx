"use client"

import { Activity, ShieldAlert, Globe, Wifi } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"

const stats = [
  {
    label: "Packets Captured",
    value: "1,284,392",
    change: "+12.5%",
    changeType: "positive" as const,
    icon: Activity,
    description: "Last 24 hours",
  },
  {
    label: "Threats Detected",
    value: "47",
    change: "-8.2%",
    changeType: "positive" as const,
    icon: ShieldAlert,
    description: "Last 24 hours",
  },
  {
    label: "Foreign Connections",
    value: "3,891",
    change: "+3.1%",
    changeType: "neutral" as const,
    icon: Globe,
    description: "Active sessions",
  },
  {
    label: "Network Uptime",
    value: "99.97%",
    change: "+0.02%",
    changeType: "positive" as const,
    icon: Wifi,
    description: "30-day average",
  },
]

export function StatCards() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.label} className="bg-card border-border">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">{stat.label}</p>
                <p className="text-2xl font-bold text-foreground">{stat.value}</p>
              </div>
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <stat.icon className="h-5 w-5 text-primary" />
              </div>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <span
                className={`text-xs font-medium ${
                  stat.changeType === "positive"
                    ? "text-emerald-500"
                    : "text-muted-foreground"
                }`}
              >
                {stat.change}
              </span>
              <span className="text-xs text-muted-foreground">{stat.description}</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
