"use client"

// ===== Consolidated Admin & Settings =====

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Settings, Users, BarChart3 } from "lucide-react"

export function SettingsPanel() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="w-5 h-5" />
          System Settings
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span>Packet Capture</span>
          <Switch defaultChecked />
        </div>
        <div className="flex items-center justify-between">
          <span>ML Detection</span>
          <Switch defaultChecked />
        </div>
        <div className="flex items-center justify-between">
          <span>Auto Block Threats</span>
          <Switch />
        </div>
        <Button className="w-full mt-4">Save Settings</Button>
      </CardContent>
    </Card>
  )
}

export function AdminPanel() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="w-5 h-5" />
          Admin Panel
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="p-2 bg-slate-50 rounded">
          <p className="text-sm font-medium">Total Users: 5</p>
          <p className="text-xs text-slate-500">2 Admins, 3 Viewers</p>
        </div>
        <Button variant="outline" className="w-full">Manage Users</Button>
        <Button variant="outline" className="w-full">View Logs</Button>
      </CardContent>
    </Card>
  )
}

export function StatsOverview() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Overview
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-blue-50 rounded">
            <p className="text-2xl font-bold text-blue-600">1.2M</p>
            <p className="text-xs text-slate-600">Packets Today</p>
          </div>
          <div className="p-3 bg-red-50 rounded">
            <p className="text-2xl font-bold text-red-600">23</p>
            <p className="text-xs text-slate-600">Threats</p>
          </div>
          <div className="p-3 bg-green-50 rounded">
            <p className="text-2xl font-bold text-green-600">98%</p>
            <p className="text-xs text-slate-600">Uptime</p>
          </div>
          <div className="p-3 bg-yellow-50 rounded">
            <p className="text-2xl font-bold text-yellow-600">12</p>
            <p className="text-xs text-slate-600">Alerts</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function ActionLogs() {
  const actions = [
    { action: "Blocked Port Scan", ip: "192.168.1.100", time: "2 mins ago" },
    { action: "Updated Filters", user: "admin", time: "1 hour ago" },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {actions.map((a: any, i: number) => (
          <div key={i} className="text-xs p-2 border-l-2 border-blue-400">
            <p className="font-medium">{a.action}</p>
            <p className="text-slate-500">
              {a.ip && `IP: ${a.ip}`} {a.user && `by ${a.user}`} - {a.time}
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
