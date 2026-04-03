"use client"
// Admin panel section for settings, summaries, and response history views.

// ===== Consolidated Admin & Settings =====

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Settings, Users, BarChart3, AlertTriangle } from "lucide-react"
import {
  createUser,
  deleteUser,
  getAdminDashboard,
  getAdminSettings,
  getNotifications,
  getUsers,
  type Notification,
  type User,
  updateAdminSettings,
} from "@/lib/api"

const DASHBOARD_REFRESH_EVENT = "chaosfaction:dashboard-refresh"

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
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [newUser, setNewUser] = useState({ email: "", role: "viewer" })

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const data = await getUsers()
      setUsers(data.users)
      setError("")
      setLoading(false)
    } catch (err) {
      setError("Failed to load users")
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  const handleCreateUser = async () => {
    if (!newUser.email.trim()) {
      alert("Please enter an email address")
      return
    }

    try {
      await createUser({ email: newUser.email.trim(), role: newUser.role as User["role"] })
      setNewUser({ email: "", role: "viewer" })
      fetchUsers()
      alert("User created successfully!")
    } catch (err) {
      alert("Failed to create user")
    }
  }

  const handleDeleteUser = async (userId: string) => {
    if (confirm("Are you sure you want to delete this user?")) {
      try {
        await deleteUser(userId)
        fetchUsers()
        alert("User deleted successfully!")
      } catch (err) {
        alert("Failed to delete user")
      }
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="w-5 h-5" />
          Admin Panel - User Management
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <div className="text-red-500 text-sm">{error}</div>}
        
        {/* User List */}
        <div className="border rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                <th scope="col" className="relative px-6 py-3">
                  <span className="sr-only">Delete</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan={3} className="text-center py-4">Loading users...</td></tr>
              ) : (
                users.map((user) => (
                  <tr key={user.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{user.email}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.role}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Button variant="destructive" size="sm" onClick={() => handleDeleteUser(user.id)}>Delete</Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Create User Form */}
        <div className="border-t pt-4 space-y-3">
          <h4 className="font-medium">Create New User</h4>
          <input
            type="email"
            placeholder="Email"
            value={newUser.email}
            onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
            className="w-full mt-1 px-3 py-2 border rounded"
          />
          <select
            value={newUser.role}
            onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
            className="w-full mt-1 px-3 py-2 border rounded"
          >
            <option value="viewer">Viewer</option>
            <option value="admin">Admin</option>
          </select>
          <Button onClick={handleCreateUser} className="w-full mt-2">Create User</Button>
        </div>
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
          <div className={`p-3 rounded ${stats.high_alert_threats > 0 ? "bg-red-50" : stats.medium_threats > 0 ? "bg-yellow-50" : "bg-green-50"}`}>
            <p className={`text-2xl font-bold ${stats.high_alert_threats > 0 ? "text-red-600" : stats.medium_threats > 0 ? "text-yellow-600" : "text-green-600"}`}>
              {stats.total_threats || 0}
            </p>
            <p className="text-xs text-slate-600">Threats Detected (No Low)</p>
          </div>
          <div className="p-3 bg-green-50 rounded">
            <p className="text-2xl font-bold text-green-600">{stats.uptime_percent || 98}%</p>
            <p className="text-xs text-slate-600">System Uptime</p>
          </div>
          <div className={`p-3 rounded ${stats.high_alert_threats > 0 ? "bg-orange-50" : "bg-blue-50"}`}>
            <p className={`text-2xl font-bold ${stats.high_alert_threats > 0 ? "text-orange-600" : "text-blue-600"}`}>
              {stats.high_alert_threats || 0}
            </p>
            <p className="text-xs text-slate-600">High Alert Threats</p>
          </div>
        </div>
        {stats.system_health !== "HEALTHY" && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-yellow-800">System {stats.system_health}</p>
              <p className="text-xs text-yellow-700">
                {stats.high_alert_threats > 0
                  ? "High alert threats detected. Review immediately."
                  : "Medium-severity threats are active. Continue monitoring."}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function ActionLogs() {
  const [actions, setActions] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    const fetchActions = async () => {
      try {
        const data = await getNotifications()
        const liveActions = (data.notifications || []).filter((notification) => notification.type === "RESPONSE_ACTION")
        setActions(liveActions)
        setError("")
      } catch (err) {
        console.error("Failed to fetch action history:", err)
        setError("Failed to load action history")
      } finally {
        setLoading(false)
      }
    }

    fetchActions()
    const interval = setInterval(fetchActions, 3000)
    const handleRefresh = () => fetchActions()
    window.addEventListener(DASHBOARD_REFRESH_EVENT, handleRefresh)

    return () => {
      clearInterval(interval)
      window.removeEventListener(DASHBOARD_REFRESH_EVENT, handleRefresh)
    }
  }, [])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {error && <p className="text-sm text-red-500">{error}</p>}
        {loading && actions.length === 0 ? (
          <p className="text-sm text-slate-500">Loading action history...</p>
        ) : actions.length === 0 ? (
          <p className="text-sm text-slate-500">No live response actions have been executed yet.</p>
        ) : (
          actions.map((action) => (
            <div key={action.id} className="rounded border-l-2 border-blue-400 bg-slate-50 p-3 text-xs">
              <p className="font-medium text-slate-900">{action.title}</p>
              <p className="mt-1 text-slate-600">{action.message}</p>
              <p className="mt-1 text-slate-400">{new Date(action.timestamp).toLocaleString()}</p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}
