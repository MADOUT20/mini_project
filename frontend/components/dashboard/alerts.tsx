"use client"

// ===== Consolidated Alerts & Notifications =====

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { AlertCircle, Archive, ChevronLeft, ChevronRight, RefreshCw } from "lucide-react"
import { getNotifications, type Notification } from "@/lib/api"

const DASHBOARD_REFRESH_EVENT = "chaosfaction:dashboard-refresh"

function getSeverityBadge(severity: string): "destructive" | "secondary" {
  if (severity === "CRITICAL") return "destructive"
  if (severity === "HIGH") return "destructive"
  return "secondary"
}

function formatTitle(notification: Notification) {
  return notification.title || notification.type.replace(/_/g, " ")
}

function useNotificationFeed() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const fetchNotifications = async () => {
    try {
      const data = await getNotifications()
      setNotifications(data.notifications || [])
      setError("")
    } catch (err) {
      console.error("Failed to fetch notifications:", err)
      setError("Failed to load notifications")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchNotifications()
    const interval = setInterval(fetchNotifications, 5000)
    const handleRefresh = () => fetchNotifications()
    window.addEventListener(DASHBOARD_REFRESH_EVENT, handleRefresh)

    return () => {
      clearInterval(interval)
      window.removeEventListener(DASHBOARD_REFRESH_EVENT, handleRefresh)
    }
  }, [])

  return { notifications, loading, error, fetchNotifications }
}

// Alert Notifications Component
export function AlertNotifications() {
  const { notifications, loading, error, fetchNotifications } = useNotificationFeed()
  const alerts = notifications.slice(0, 4)
  const [activeIndex, setActiveIndex] = useState(0)

  useEffect(() => {
    if (alerts.length === 0) {
      setActiveIndex(0)
      return
    }

    setActiveIndex((currentIndex) => Math.min(currentIndex, alerts.length - 1))
  }, [alerts.length])

  const activeAlert = alerts[activeIndex]

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          Active Alerts
        </CardTitle>
        <Button size="sm" variant="ghost" onClick={fetchNotifications}>
          <RefreshCw className="w-4 h-4" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {error && <p className="text-sm text-red-500">{error}</p>}
        {loading && alerts.length === 0 ? (
          <p className="text-sm text-slate-500">Loading alerts...</p>
        ) : alerts.length === 0 ? (
          <p className="text-sm text-slate-500">No active alerts right now.</p>
        ) : (
          <>
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs text-slate-500">
                Alert {activeIndex + 1} of {alerts.length}
              </p>
              {alerts.length > 1 && (
                <div className="flex items-center gap-1">
                  <Button
                    size="icon"
                    variant="outline"
                    className="h-8 w-8"
                    onClick={() => setActiveIndex((currentIndex) => Math.max(0, currentIndex - 1))}
                    disabled={activeIndex === 0}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    <span className="sr-only">Previous alert</span>
                  </Button>
                  <Button
                    size="icon"
                    variant="outline"
                    className="h-8 w-8"
                    onClick={() => setActiveIndex((currentIndex) => Math.min(alerts.length - 1, currentIndex + 1))}
                    disabled={activeIndex === alerts.length - 1}
                  >
                    <ChevronRight className="h-4 w-4" />
                    <span className="sr-only">Next alert</span>
                  </Button>
                </div>
              )}
            </div>
            <div className="flex min-h-36 items-start justify-between gap-3 rounded-xl bg-slate-50 p-4">
              <div className="flex-1 space-y-2">
                <p className="font-medium text-sm">{formatTitle(activeAlert)}</p>
                <p className="text-xs leading-5 text-slate-500">{activeAlert.message}</p>
                <p className="text-xs text-slate-400">{new Date(activeAlert.timestamp).toLocaleString()}</p>
              </div>
              <Badge variant={getSeverityBadge(activeAlert.severity)}>
                {activeAlert.severity}
              </Badge>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

// Notification Archive Component
export function NotificationArchive() {
  const { notifications, loading, error, fetchNotifications } = useNotificationFeed()

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Archive className="w-5 h-5" />
          Notification Activity
        </CardTitle>
        <Button size="sm" variant="ghost" onClick={fetchNotifications}>
          <RefreshCw className="w-4 h-4" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {error && <p className="text-sm text-red-500">{error}</p>}
        {loading && notifications.length === 0 ? (
          <p className="text-sm text-slate-500">Loading notifications...</p>
        ) : notifications.length === 0 ? (
          <p className="text-slate-500">No notification history yet.</p>
        ) : (
          <ScrollArea className="h-96 pr-3">
            <div className="space-y-2">
              {notifications.map((alert) => (
                <div key={alert.id} className="space-y-1 rounded border p-3 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-medium">{formatTitle(alert)}</p>
                    <Badge variant={getSeverityBadge(alert.severity)}>{alert.severity}</Badge>
                  </div>
                  <p className="text-slate-600">{alert.message}</p>
                  <p className="text-xs text-slate-400">{new Date(alert.timestamp).toLocaleString()}</p>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}
