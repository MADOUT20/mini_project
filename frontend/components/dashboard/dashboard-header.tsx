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
  const [archivedAlerts, setArchivedAlerts] = useState<string[]>([])
  const [showArchived, setShowArchived] = useState(false)
  const [alerts, setAlerts] = useState([
    {
      id: "alert-1",
      alertType: "malicious" as const,
      userIp: "192.168.1.105",
      threat: "Trojan.GenericKD.5589823",
      timestamp: "2 min ago",
      actionTaken: "blocked" as const,
      isMalicious: true,
    },
    {
      id: "alert-2",
      alertType: "high-risk" as const,
      userIp: "10.0.0.42",
      threat: "Port Scan Detected",
      timestamp: "5 min ago",
      isMalicious: false,
    },
  ])

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
              {alerts.length > 0 && (
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
                  setArchivedAlerts([...archivedAlerts, ...alerts.map(a => a.id)])
                  setAlerts([])
                }}
              >
                Clear All
              </Button>
            )}
            <DropdownMenuSeparator />
            {(showArchived ? archivedAlerts.length > 0 : alerts.length > 0) ? (
              <div className="max-h-96 overflow-y-auto space-y-2 p-2">
                {(showArchived ? [] : alerts).map(alert => {
                  const isMalicious = alert.alertType === "malicious"
                  const alertColor = isMalicious
                    ? "border-destructive/30 bg-destructive/5"
                    : alert.alertType === "high-risk"
                      ? "border-warning/30 bg-warning/5"
                      : "border-yellow-500/30 bg-yellow-500/5"

                  return (
                    <div key={alert.id} className={`p-3 rounded-lg border ${alertColor} space-y-2`}>
                      <div className="flex items-center justify-between">
                        <Badge
                          variant="outline"
                          className={
                            isMalicious
                              ? "bg-destructive text-destructive-foreground border-destructive"
                              : alert.alertType === "high-risk"
                                ? "bg-warning text-warning-foreground border-warning"
                                : "bg-yellow-600 text-yellow-50 border-yellow-600"
                          }
                        >
                          {alert.alertType.toUpperCase()}
                        </Badge>
                        <span className="text-xs text-muted-foreground">{alert.timestamp}</span>
                      </div>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between items-start">
                          <span className="text-muted-foreground">User IP:</span>
                          <code className="bg-secondary/50 px-2 py-0.5 rounded text-foreground font-mono text-xs">
                            {alert.userIp}
                          </code>
                        </div>
                        <div className="flex justify-between items-start">
                          <span className="text-muted-foreground">Threat:</span>
                          <span className="font-medium text-foreground text-right max-w-[60%]">
                            {alert.threat}
                          </span>
                        </div>
                      </div>
                      {isMalicious && (
                        <div className="flex items-center gap-2 p-2 rounded bg-destructive/10 border border-destructive/20 text-xs">
                          <AlertCircle className="h-3 w-3 text-destructive flex-shrink-0" />
                          <span className="text-destructive font-medium">Direct Block Applied</span>
                        </div>
                      )}
                      <button
                        onClick={() => {
                          setArchivedAlerts([...archivedAlerts, alert.id])
                          setAlerts(alerts.filter(a => a.id !== alert.id))
                        }}
                        className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                      >
                        Archive
                      </button>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="p-6 text-center">
                <p className="text-sm text-muted-foreground">No active alerts</p>
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
