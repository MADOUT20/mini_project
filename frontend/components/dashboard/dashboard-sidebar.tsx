"use client"

import { useState } from "react"
import Link from "next/link"
import {
  Shield,
  LayoutDashboard,
  Activity,
  Search,
  ShieldAlert,
  Globe,
  CheckCircle2,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Archive,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

const navItems = [
  { icon: LayoutDashboard, label: "Overview", id: "overview" },
  { icon: Activity, label: "Packet Capture", id: "packets" },
  { icon: Search, label: "Packet Inspection", id: "inspection" },
  { icon: ShieldAlert, label: "Threat Detection", id: "threats" },
  { icon: Globe, label: "Traffic Analysis", id: "traffic" },
  { icon: CheckCircle2, label: "Action Taken History", id: "actions" },
  { icon: Archive, label: "Notification Archive", id: "archive" },
  { icon: Settings, label: "Settings", id: "settings" },
]

interface DashboardSidebarProps {
  activeTab: string
  onTabChange: (tab: string) => void
}

export function DashboardSidebar({ activeTab, onTabChange }: DashboardSidebarProps) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          "flex flex-col border-r border-sidebar-border bg-sidebar transition-all duration-200",
          collapsed ? "w-16" : "w-60"
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center gap-3 border-b border-sidebar-border px-4">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary">
            <Shield className="h-5 w-5 text-primary-foreground" />
          </div>
          {!collapsed && (
            <span className="text-lg font-bold text-sidebar-foreground">NetGuard</span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-3">
          {navItems.map((item) => {
            const isActive = activeTab === item.id
            const button = (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-primary"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                )}
              >
                <item.icon className="h-4.5 w-4.5 shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </button>
            )

            if (collapsed) {
              return (
                <Tooltip key={item.id}>
                  <TooltipTrigger asChild>{button}</TooltipTrigger>
                  <TooltipContent side="right" className="bg-popover text-popover-foreground">
                    {item.label}
                  </TooltipContent>
                </Tooltip>
              )
            }
            return button
          })}
        </nav>

        {/* Bottom */}
        <div className="border-t border-sidebar-border p-3 space-y-1">
          {collapsed ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <Link href="/login" className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-sidebar-foreground hover:bg-sidebar-accent transition-colors">
                  <LogOut className="h-4.5 w-4.5 shrink-0" />
                </Link>
              </TooltipTrigger>
              <TooltipContent side="right" className="bg-popover text-popover-foreground">Logout</TooltipContent>
            </Tooltip>
          ) : (
            <Link href="/login" className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-sidebar-foreground hover:bg-sidebar-accent transition-colors">
              <LogOut className="h-4.5 w-4.5 shrink-0" />
              <span>Logout</span>
            </Link>
          )}
        </div>

        {/* Collapse Toggle */}
        <div className="border-t border-sidebar-border p-2">
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-sidebar-foreground hover:bg-sidebar-accent"
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>
      </aside>
    </TooltipProvider>
  )
}
