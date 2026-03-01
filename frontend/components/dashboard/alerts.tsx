"use client"

// ===== Consolidated Alerts & Notifications =====

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AlertCircle, Archive, Trash2 } from "lucide-react"
import { useState } from "react"

// Alert Notifications Component
export function AlertNotifications() {
  const [alerts, setAlerts] = useState([
    { id: 1, type: "PORT_SCAN", severity: "HIGH", time: "2 mins ago" },
    { id: 2, type: "SUSPICIOUS_TRAFFIC", severity: "MEDIUM", time: "5 mins ago" },
  ])

  const archiveAlert = (id: number) => setAlerts(alerts.filter((a: any) => a.id !== id))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          Active Alerts
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {alerts.map((alert: any) => (
          <div key={alert.id} className="flex items-center justify-between p-3 bg-slate-50 rounded">
            <div className="flex-1">
              <p className="font-medium">{alert.type}</p>
              <p className="text-sm text-slate-500">{alert.time}</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={alert.severity === "HIGH" ? "destructive" : "secondary"}>
                {alert.severity}
              </Badge>
              <Button size="sm" variant="ghost" onClick={() => archiveAlert(alert.id)}>
                <Archive className="w-4 h-4" />
              </Button>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

// Notification Archive Component
export function NotificationArchive() {
  const [archivedAlerts] = useState([
    { id: 1, type: "RESOLVED", status: "BLOCKED", time: "1 hour ago" },
  ])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Archived Alerts</CardTitle>
      </CardHeader>
      <CardContent>
        {archivedAlerts.length === 0 ? (
          <p className="text-slate-500">No archived alerts</p>
        ) : (
          <div className="space-y-2">
            {archivedAlerts.map((alert: any) => (
              <div key={alert.id} className="p-2 text-sm border rounded">
                {alert.type} - {alert.status}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
