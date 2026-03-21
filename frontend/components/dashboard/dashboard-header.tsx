"use client"

import { useState, useEffect } from "react"
import { Bell, User, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ThemeToggle } from "@/components/theme-toggle"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { UserProfileModal } from "@/components/user-profile-modal"
import Link from "next/link"

const tabLabels: Record<string, string> = {
  overview: "Dashboard Overview",
  packets: "Packet Capture Module",
  inspection: "Deep Packet Inspection",
  threats: "Threat Detection",
  traffic: "Traffic Analysis",
  actions: "Action Taken History",
  archive: "Notification Archive",
  settings: "System Settings",
}

interface DashboardHeaderProps {
  activeTab: string
  onTabChange?: (tab: string) => void
}

export function DashboardHeader({ activeTab, onTabChange }: DashboardHeaderProps) {
  const [profileOpen, setProfileOpen] = useState(false)
  const [userName, setUserName] = useState("Admin User")
  const [archivedAlerts, setArchivedAlerts] = useState<any[]>([])
  const [showArchived, setShowArchived] = useState(false)
  const [alerts, setAlerts] = useState<any[]>([])
  const [loadingAlerts, setLoadingAlerts] = useState(true)

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const { getNotifications } = await import("@/lib/api")
        const data = await getNotifications()
        setAlerts(data.notifications || [])
        setLoadingAlerts(false)
      } catch (err) {
        console.error("Failed to fetch notifications:", err)
        setLoadingAlerts(false)
      }
    }

    fetchAlerts()
    const interval = setInterval(fetchAlerts, 3000)
    return () => clearInterval(interval)
  }, [])

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-card px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-foreground">
          {tabLabels[activeTab] || "Dashboard"}
        </h1>
        <Badge variant="outline" className="hidden sm:inline-flex text-xs border-emerald-500/30 text-emerald-500">
          System Online
        </Badge>
      </div>
      <div className="flex items-center gap-2">
        <ThemeToggle />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-5 w-5" />
              {!loadingAlerts && alerts.length > 0 && (
                <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[10px] text-destructive-foreground font-semibold">
                  {alerts.length}
                </span>
              )}
              <span className="sr-only">Notifications</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-96">
            <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
              <Button
                variant={showArchived ? "ghost" : "default"}
                size="sm"
                className="h-6 text-xs"
                onClick={() => setShowArchived(false)}
              >
                Active ({alerts.length})
              </Button>
              <Button
                variant={showArchived ? "default" : "ghost"}
                size="sm"
                className="h-6 text-xs"
                onClick={() => setShowArchived(true)}
              >
                Archive ({archivedAlerts.length})
              </Button>
            </div>
            {!showArchived && alerts.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="w-full h-6 px-2 text-xs text-muted-foreground hover:text-foreground justify-center"
                onClick={() => {
                  setArchivedAlerts([...archivedAlerts, ...alerts])
                  setAlerts([])
                }}
              >
                Clear All
              </Button>
            )}
            <DropdownMenuSeparator />
            {loadingAlerts ? (
              <div className="p-4 text-center text-sm text-slate-500">Loading notifications...</div>
            ) : (showArchived ? archivedAlerts.length > 0 : alerts.length > 0) ? (
              <div className="max-h-96 overflow-y-auto space-y-2 p-2">
                {(showArchived ? archivedAlerts : alerts).map((alert) => {
                  const severity = alert.severity || "MEDIUM"
                  const alertColor = severity === "CRITICAL"
                    ? "border-destructive/30 bg-destructive/5"
                    : severity === "HIGH"
                      ? "border-red-500/30 bg-red-500/5"
                      : severity === "MEDIUM"
                        ? "border-yellow-500/30 bg-yellow-500/5"
                        : "border-blue-500/30 bg-blue-500/5"

                  return (
                    <div key={alert.id} className={`p-3 rounded-lg border ${alertColor} space-y-2`}>
                      <div className="flex items-center justify-between">
                        <Badge
                          variant="outline"
                          className={
                            severity === "CRITICAL"
                              ? "bg-destructive text-destructive-foreground border-destructive"
                              : severity === "HIGH"
                                ? "bg-red-600 text-red-50 border-red-600"
                                : severity === "MEDIUM"
                                  ? "bg-yellow-600 text-yellow-50 border-yellow-600"
                                  : "bg-blue-600 text-blue-50 border-blue-600"
                          }
                        >
                          {severity}
                        </Badge>
                        <span className="text-xs text-muted-foreground">{alert.timestamp}</span>
                      </div>
                      <div className="space-y-1 text-sm">
                        <p className="font-medium text-foreground">{alert.title}</p>
                        <p className="text-xs text-muted-foreground">{alert.message}</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="p-4 text-center text-sm text-slate-500">
                {showArchived ? "No archived notifications" : "All clear! No active threats."}
              </div>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                <User className="h-4 w-4 text-primary" />
              </div>
              <span className="sr-only">User menu</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <div className="px-3 py-2">
              <p className="text-sm font-medium text-foreground">{userName}</p>
              <p className="text-xs text-muted-foreground">admin@netguard.io</p>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => setProfileOpen(true)}>
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onTabChange?.("settings")}>
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/login">Logout</Link>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* User Profile Modal */}
      <UserProfileModal 
        open={profileOpen} 
        onOpenChange={setProfileOpen}
        onNameChange={setUserName}
      />
    </header>
  )
}
