"use client"

// ===== Consolidated Alerts & Notifications =====

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AlertCircle, Archive, RefreshCw } from "lucide-react"
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
          alerts.map((alert) => (
            <div key={alert.id} className="flex items-start justify-between gap-3 p-3 bg-slate-50 rounded">
              <div className="flex-1 space-y-1">
                <p className="font-medium text-sm">{formatTitle(alert)}</p>
                <p className="text-xs text-slate-500">{alert.message}</p>
                <p className="text-xs text-slate-400">{new Date(alert.timestamp).toLocaleString()}</p>
              </div>
              <Badge variant={getSeverityBadge(alert.severity)}>
                {alert.severity}
              </Badge>
            </div>
          ))
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
          <div className="space-y-2">
            {notifications.map((alert) => (
              <div key={alert.id} className="p-3 text-sm border rounded space-y-1">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium">{formatTitle(alert)}</p>
                  <Badge variant={getSeverityBadge(alert.severity)}>{alert.severity}</Badge>
                </div>
                <p className="text-slate-600">{alert.message}</p>
                <p className="text-xs text-slate-400">{new Date(alert.timestamp).toLocaleString()}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
