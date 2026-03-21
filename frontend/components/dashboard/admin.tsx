"use client"

// ===== Consolidated Admin & Settings =====

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Settings, Users, BarChart3, AlertTriangle } from "lucide-react"
import { getAdminDashboard, getAdminSettings, updateAdminSettings } from "@/lib/api"

export function SettingsPanel() {
  const [settings, setSettings] = useState<any>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await getAdminSettings()
        setSettings(data)
        setLoading(false)
      } catch (err) {
        setError("Failed to load settings")
        setLoading(false)
      }
    }
    fetchSettings()
  }, [])

  const handleSaveSettings = async () => {
    try {
      await updateAdminSettings({
        pps_threshold: settings.pps_threshold,
        port_scan_threshold: settings.port_scan_threshold,
        alert_level: settings.alert_level,
      })
      alert("Settings saved successfully!")
    } catch (err) {
      alert("Failed to save settings")
    }
  }

  if (loading) return <Card><CardContent className="pt-6">Loading settings...</CardContent></Card>

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="w-5 h-5" />
          System Settings
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <div className="text-red-500 text-sm">{error}</div>}
        <div className="flex items-center justify-between">
          <span>Packet Capture</span>
          <Switch checked={settings.capture_enabled} disabled />
        </div>
        <div className="flex items-center justify-between">
          <span>Anomaly Detection</span>
          <Switch checked={settings.anomaly_detection_enabled} disabled />
        </div>
        <div className="flex items-center justify-between">
          <span>Auto Block Threats</span>
          <Switch checked={settings.auto_block} disabled />
        </div>
        <div className="border-t pt-4">
          <label className="text-sm font-medium">PPS Threshold</label>
          <input
            type="number"
            value={settings.pps_threshold || 1000}
            onChange={(e) => setSettings({ ...settings, pps_threshold: parseInt(e.target.value) })}
            className="w-full mt-1 px-3 py-2 border rounded"
          />
        </div>
        <div>
          <label className="text-sm font-medium">Port Scan Threshold</label>
          <input
            type="number"
            value={settings.port_scan_threshold || 50}
            onChange={(e) => setSettings({ ...settings, port_scan_threshold: parseInt(e.target.value) })}
            className="w-full mt-1 px-3 py-2 border rounded"
          />
        </div>
        <Button onClick={handleSaveSettings} className="w-full mt-4">Save Settings</Button>
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
          <p className="text-sm font-medium">System Status: Operational</p>
          <p className="text-xs text-slate-500">All services running normally</p>
        </div>
        <Button variant="outline" className="w-full">View Logs</Button>
      </CardContent>
    </Card>
  )
}

export function StatsOverview() {
  const [stats, setStats] = useState<any>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const dashboard = await getAdminDashboard()
        setStats(dashboard)
        setLoading(false)
      } catch (err: any) {
        console.error("Failed to fetch dashboard:", err)
        setError("Failed to load stats - Backend not responding")
        setLoading(false)
      }
    }
    
    // Fetch immediately and then every 5 seconds
    fetchStats()
    const interval = setInterval(fetchStats, 5000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">Connecting to backend...</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Overview
          {error && <Badge variant="destructive" className="ml-auto">{error}</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-blue-50 rounded">
            <p className="text-2xl font-bold text-blue-600">{(stats.total_packets || 0).toLocaleString()}</p>
            <p className="text-xs text-slate-600">Packets Captured</p>
          </div>
          <div className={`p-3 rounded ${stats.critical_threats > 0 ? "bg-red-50" : "bg-green-50"}`}>
            <p className={`text-2xl font-bold ${stats.critical_threats > 0 ? "text-red-600" : "text-green-600"}`}>
              {stats.total_threats || 0}
            </p>
            <p className="text-xs text-slate-600">Threats Detected</p>
          </div>
          <div className="p-3 bg-green-50 rounded">
            <p className="text-2xl font-bold text-green-600">{stats.uptime_percent || 98}%</p>
            <p className="text-xs text-slate-600">System Uptime</p>
          </div>
          <div className={`p-3 rounded ${stats.critical_threats > 0 ? "bg-yellow-50" : "bg-blue-50"}`}>
            <p className={`text-2xl font-bold ${stats.critical_threats > 0 ? "text-yellow-600" : "text-blue-600"}`}>
              {stats.critical_threats || 0}
            </p>
            <p className="text-xs text-slate-600">Critical Threats</p>
          </div>
        </div>
        {stats.system_health === "WARNING" && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-yellow-800">System Warning</p>
              <p className="text-xs text-yellow-700">Critical threats detected. Review immediately.</p>
            </div>
          </div>
        )}
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
