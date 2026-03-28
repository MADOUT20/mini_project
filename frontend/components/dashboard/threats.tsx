"use client"

// ===== Consolidated Threats =====

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AlertTriangle, ChevronLeft, ChevronRight, MapPin, RefreshCw, Shield, Smartphone, Wifi, Zap } from "lucide-react"
import {
  clearBlockedSites,
  getBlockedSites,
  getProxyStatus,
  getThreats,
  respondToThreat,
  unblockSite,
  Threat,
  type BlockedSite,
  type ProxyClient,
} from "@/lib/api"

const DASHBOARD_REFRESH_EVENT = "chaosfaction:dashboard-refresh"

function emitDashboardRefresh() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(DASHBOARD_REFRESH_EVENT))
  }
}

function getSeverityClass(severity: Threat["severity"]) {
  if (severity === "CRITICAL") return "bg-red-50 border-red-200"
  if (severity === "HIGH") return "bg-orange-50 border-orange-200"
  if (severity === "MEDIUM") return "bg-yellow-50 border-yellow-200"
  return "bg-blue-50 border-blue-200"
}

function formatStatus(status: string) {
  return status.replace(/_/g, " ").replace(/\b\w/g, (match) => match.toUpperCase())
}

function formatThreatType(type: string) {
  return type.replace(/_/g, " ").replace(/\b\w/g, (match) => match.toUpperCase())
}

function getSeverityRank(severity: Threat["severity"]) {
  if (severity === "CRITICAL") return 4
  if (severity === "HIGH") return 3
  if (severity === "MEDIUM") return 2
  return 1
}

function isPrivateNetworkAddress(value?: string) {
  if (!value) {
    return false
  }

  if (value.startsWith("10.") || value.startsWith("192.168.")) {
    return true
  }

  const octets = value.split(".")
  if (octets.length < 2 || octets[0] !== "172") {
    return false
  }

  const secondOctet = Number(octets[1])
  return Number.isFinite(secondOctet) && secondOctet >= 16 && secondOctet <= 31
}

function formatThreatSource(sourceIp: string) {
  if (isPrivateNetworkAddress(sourceIp)) {
    return `Local device ${sourceIp}`
  }
  return sourceIp
}

interface ThreatDetectionPanelProps {
  excludeLow?: boolean
}

export function ThreatDetectionPanel({ excludeLow = false }: ThreatDetectionPanelProps) {
  const [threats, setThreats] = useState<Threat[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [activeIndex, setActiveIndex] = useState(0)

  const fetchThreats = async () => {
    try {
      setLoading(true)
      const data = await getThreats("all")
      setThreats((data.threats || []).filter((threat) => threat.status !== "ignored"))
      setError("")
    } catch (err: any) {
      console.error("Failed to fetch threats:", err)
      setError("Failed to load threats")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchThreats()
    const interval = setInterval(fetchThreats, 5000)
    const handleRefresh = () => fetchThreats()
    window.addEventListener(DASHBOARD_REFRESH_EVENT, handleRefresh)

    return () => {
      clearInterval(interval)
      window.removeEventListener(DASHBOARD_REFRESH_EVENT, handleRefresh)
    }
  }, [])

  const handleThreatAction = async (threatId: string, action: string) => {
    try {
      const result = await respondToThreat(threatId, action)
      setMessage(result.message || `Threat ${action.toLowerCase()} completed`)
      emitDashboardRefresh()
      await fetchThreats()
    } catch (err: any) {
      setMessage(err?.message || "Failed to respond to threat")
    }
  }

  const visibleThreats = threats
    .filter((threat) => !excludeLow || threat.severity !== "LOW")
    .sort((left, right) => {
      const severityDifference = getSeverityRank(right.severity) - getSeverityRank(left.severity)
      if (severityDifference !== 0) {
        return severityDifference
      }
      return new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime()
    })

  useEffect(() => {
    if (visibleThreats.length === 0) {
      setActiveIndex(0)
      return
    }

    setActiveIndex((currentIndex) => Math.min(currentIndex, visibleThreats.length - 1))
  }, [visibleThreats.length])

  const activeThreat = visibleThreats[activeIndex]

  if (loading && threats.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            Threats Detected
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">Loading threats...</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-500" />
          Threat Watch ({visibleThreats.length})
        </CardTitle>
        <Button size="sm" variant="ghost" onClick={fetchThreats}>
          <RefreshCw className="w-4 h-4" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {error && <div className="text-red-500 text-sm">{error}</div>}
        {message && <div className="text-sm text-slate-600">{message}</div>}

        {visibleThreats.length === 0 ? (
          <div className="p-3 bg-green-50 border border-green-200 rounded text-center">
            <p className="text-sm font-medium text-green-700">
              {excludeLow ? "No medium or high threats detected" : "No confirmed threats detected"}
            </p>
            <p className="text-xs text-green-600">
              {excludeLow ? "Overview only shows medium, high, and critical alerts." : "Only confirmed detections are shown here."}
            </p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs text-slate-500">
                Threat {activeIndex + 1} of {visibleThreats.length}
              </p>
              {visibleThreats.length > 1 && (
                <div className="flex items-center gap-1">
                  <Button
                    size="icon"
                    variant="outline"
                    className="h-8 w-8"
                    onClick={() => setActiveIndex((currentIndex) => Math.max(0, currentIndex - 1))}
                    disabled={activeIndex === 0}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    <span className="sr-only">Previous threat</span>
                  </Button>
                  <Button
                    size="icon"
                    variant="outline"
                    className="h-8 w-8"
                    onClick={() => setActiveIndex((currentIndex) => Math.min(visibleThreats.length - 1, currentIndex + 1))}
                    disabled={activeIndex === visibleThreats.length - 1}
                  >
                    <ChevronRight className="h-4 w-4" />
                    <span className="sr-only">Next threat</span>
                  </Button>
                </div>
              )}
            </div>
            <div
              key={activeThreat.id}
              className={`rounded-2xl border p-4 shadow-sm ${getSeverityClass(activeThreat.severity)}`}
            >
              <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-slate-900">{formatThreatType(activeThreat.type)}</p>
                  <p className="text-xs text-slate-600">
                    {isPrivateNetworkAddress(activeThreat.source_ip) ? "Detected from a local Wi-Fi device" : "Detected from network traffic"}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2 sm:justify-end">
                  <Badge
                    variant={activeThreat.severity === "CRITICAL" ? "destructive" : "default"}
                    className={
                      activeThreat.severity === "HIGH"
                        ? "bg-orange-600"
                        : activeThreat.severity === "MEDIUM"
                          ? "bg-yellow-600"
                          : "bg-blue-600"
                    }
                  >
                    {activeThreat.severity}
                  </Badge>
                  <Badge variant="outline">{formatStatus(activeThreat.status)}</Badge>
                </div>
              </div>

              <div className="mb-3 grid gap-2 sm:grid-cols-2">
                <div className="rounded-xl bg-white/75 px-3 py-2">
                  <p className="text-[11px] uppercase tracking-wide text-slate-500">Device</p>
                  <p className="mt-1 flex items-center gap-2 text-sm font-medium text-slate-900">
                    <Smartphone className="h-4 w-4 text-slate-500" />
                    {formatThreatSource(activeThreat.source_ip)}
                  </p>
                </div>
                <div className="rounded-xl bg-white/75 px-3 py-2">
                  <p className="text-[11px] uppercase tracking-wide text-slate-500">Target</p>
                  <p className="mt-1 break-all text-sm font-medium text-slate-900">
                    {activeThreat.destination_host || activeThreat.destination_ip || "Unknown target"}
                  </p>
                </div>
                {activeThreat.destination_ip && (
                  <div className="rounded-xl bg-white/75 px-3 py-2">
                    <p className="text-[11px] uppercase tracking-wide text-slate-500">Resolved IP</p>
                    <p className="mt-1 flex items-center gap-2 text-sm font-medium text-slate-900">
                      <MapPin className="h-4 w-4 text-slate-500" />
                      {activeThreat.destination_ip}
                      {activeThreat.destination_port ? `:${activeThreat.destination_port}` : ""}
                    </p>
                  </div>
                )}
                <div className="rounded-xl bg-white/75 px-3 py-2">
                  <p className="text-[11px] uppercase tracking-wide text-slate-500">Confidence</p>
                  <p className="mt-1 text-sm font-medium text-slate-900">
                    {(activeThreat.threat_score * 100).toFixed(0)}%
                  </p>
                </div>
              </div>

              <div className="rounded-xl bg-white/70 px-3 py-3">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Alert message</p>
                <p className="mt-2 text-sm text-slate-700">{activeThreat.description}</p>
              </div>

              {activeThreat.evidence && activeThreat.evidence.length > 0 && (
                <div className="mb-3 mt-3 space-y-1">
                  {activeThreat.evidence.slice(0, 2).map((item, index) => (
                    <p key={`${activeThreat.id}-evidence-${index}`} className="text-xs text-slate-500">
                      • {item}
                    </p>
                  ))}
                </div>
              )}
              <div className="flex flex-col gap-2 sm:flex-row">
                <Button
                  size="sm"
                  className="bg-red-600 text-xs hover:bg-red-700 sm:flex-1"
                  onClick={() => handleThreatAction(activeThreat.id, "BLOCK")}
                  disabled={activeThreat.status === "blocked"}
                >
                  {activeThreat.status === "blocked" ? "Blocked" : "Block"}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="text-xs sm:flex-1"
                  onClick={() => handleThreatAction(activeThreat.id, "INVESTIGATE")}
                >
                  Investigate
                </Button>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

export function ObservedDevicesCard() {
  const [clients, setClients] = useState<ProxyClient[]>([])
  const [proxyListening, setProxyListening] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchProxyDevices = async () => {
      try {
        const status = await getProxyStatus()
        setProxyListening(status.enabled && status.listening)
        setClients(status.clients || [])
      } catch (error) {
        console.error("Failed to fetch proxy status:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchProxyDevices()
    const interval = setInterval(fetchProxyDevices, 3000)
    return () => clearInterval(interval)
  }, [])

  const latestClient = clients[0]
  const hasActiveClient = clients.length > 0

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wifi className="h-5 w-5" />
          Observed Devices
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="rounded-2xl bg-slate-50 p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-slate-900">
                {hasActiveClient ? "Device currently online" : proxyListening ? "Waiting for phone traffic" : "Phone proxy is offline"}
              </p>
              <p className="text-xs text-slate-500">
                {hasActiveClient
                  ? "This device sent traffic through the monitored proxy within the last 15 seconds."
                  : proxyListening
                    ? "A device is marked live only when traffic is seen in the last 15 seconds."
                    : "Start capture mode to watch phone traffic."}
              </p>
            </div>
            <Badge
              variant={hasActiveClient ? "default" : "outline"}
              className={hasActiveClient ? "bg-emerald-600" : proxyListening ? "bg-amber-600 text-white" : ""}
            >
              {hasActiveClient ? "LIVE" : proxyListening ? "IDLE" : "OFF"}
            </Badge>
          </div>
        </div>

        {loading ? (
          <p className="text-sm text-slate-500">Loading observed devices...</p>
        ) : latestClient ? (
          <div className="space-y-2 rounded-2xl border border-border bg-white/70 p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">Latest device</p>
            <p className="flex items-center gap-2 text-sm font-semibold text-slate-900">
              <Smartphone className="h-4 w-4 text-slate-500" />
              {latestClient.source_ip}
            </p>
            <p className="text-sm text-slate-600">
              Last host: {latestClient.last_host || "Awaiting website visit"}
            </p>
            {latestClient.last_destination_ip && (
              <p className="text-sm text-slate-600">
                Last IP: {latestClient.last_destination_ip}
                {latestClient.last_destination_port ? `:${latestClient.last_destination_port}` : ""}
              </p>
            )}
            <p className="text-xs text-slate-500">
              Requests seen: {latestClient.request_count}
            </p>
            {latestClient.last_seen && (
              <p className="text-xs text-slate-500">
                Last seen: {new Date(latestClient.last_seen).toLocaleTimeString()}
              </p>
            )}
          </div>
        ) : (
          <p className="text-sm text-slate-500">
            No phone traffic seen yet. Open a watched site from the phone through the proxy.
          </p>
        )}
      </CardContent>
    </Card>
  )
}

export function BlockedSitesCard() {
  const [blockedSites, setBlockedSites] = useState<BlockedSite[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")
  const [busyKey, setBusyKey] = useState<string | null>(null)

  const fetchBlockedSites = async () => {
    try {
      const data = await getBlockedSites()
      setBlockedSites(data.blocked_sites || [])
      setError("")
    } catch (err) {
      console.error("Failed to fetch blocked sites:", err)
      setError("Failed to load blocked sites")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBlockedSites()
    const interval = setInterval(fetchBlockedSites, 4000)
    const handleRefresh = () => fetchBlockedSites()
    window.addEventListener(DASHBOARD_REFRESH_EVENT, handleRefresh)

    return () => {
      clearInterval(interval)
      window.removeEventListener(DASHBOARD_REFRESH_EVENT, handleRefresh)
    }
  }, [])

  const handleUnblock = async (domain: string) => {
    setBusyKey(domain)
    try {
      const result = await unblockSite(domain)
      setMessage(result.message || `Unblocked ${domain}`)
      emitDashboardRefresh()
      await fetchBlockedSites()
    } catch (err: any) {
      setMessage(err?.message || "Failed to unblock site")
    } finally {
      setBusyKey(null)
    }
  }

  const handleClearAll = async () => {
    setBusyKey("__all__")
    try {
      const result = await clearBlockedSites()
      setMessage(result.message || "Cleared blocked sites")
      emitDashboardRefresh()
      await fetchBlockedSites()
    } catch (err: any) {
      setMessage(err?.message || "Failed to clear blocked sites")
    } finally {
      setBusyKey(null)
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-5 h-5" />
          Blocked Sites
        </CardTitle>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="ghost" onClick={fetchBlockedSites}>
            <RefreshCw className="w-4 h-4" />
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleClearAll}
            disabled={busyKey !== null || blockedSites.length === 0}
          >
            {busyKey === "__all__" ? "Clearing..." : "Clear All"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-xs text-slate-500">
          Blocks here only affect phone traffic going through the monitored proxy. To restore browsing,
          unblock the site here or set the phone Wi-Fi proxy back to <span className="font-medium">None</span>.
        </p>
        {error && <p className="text-sm text-red-500">{error}</p>}
        {message && <p className="text-sm text-slate-600">{message}</p>}
        {loading && blockedSites.length === 0 ? (
          <p className="text-sm text-slate-500">Loading blocked sites...</p>
        ) : blockedSites.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-medium text-slate-700">No websites are blocked right now.</p>
            <p className="mt-1 text-xs text-slate-500">
              If you block a malicious site from the dashboard, it will appear here until you unblock it.
            </p>
          </div>
        ) : (
          blockedSites.map((site) => (
            <div key={site.domain} className="rounded-xl border bg-slate-50 p-3">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-slate-900">{site.domain}</p>
                  <p className="text-xs text-slate-500">
                    Block reason: {site.reason || "Manual block"}
                  </p>
                  {site.blocked_at && (
                    <p className="text-xs text-slate-400">
                      Blocked at {new Date(site.blocked_at).toLocaleString()}
                    </p>
                  )}
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleUnblock(site.domain)}
                  disabled={busyKey !== null}
                >
                  {busyKey === site.domain ? "Unblocking..." : "Unblock"}
                </Button>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}

export function ThreatResponsePanel() {
  const [busyAction, setBusyAction] = useState<string | null>(null)
  const [message, setMessage] = useState("")

  const handleQuickResponse = async (action: string) => {
    setBusyAction(action)
    try {
      const data = await getThreats("active")
      const threats = data.threats || []
      
      if (threats.length > 0) {
        const threat = threats[0]
        const result = await respondToThreat(threat.id, action)
        setMessage(result.message || `Quick action '${action}' executed`)
        emitDashboardRefresh()
      } else {
        setMessage("No active threats to respond to right now")
      }
    } catch (err) {
      setMessage("Failed to execute action")
    }
    setBusyAction(null)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="w-5 h-5" />
          Response Actions
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-xs text-slate-500">
          Blocking here affects phone browsing only when the phone is using the Mac proxy. It does not
          change your system firewall.
        </p>
        <p className="text-xs text-slate-500">
          If you block a website by mistake, use the Blocked Sites card to unblock it immediately.
        </p>
        {message && <p className="text-sm text-slate-600">{message}</p>}
        <Button 
          className="w-full" 
          onClick={() => handleQuickResponse("BLOCK")}
          disabled={busyAction !== null}
        >
          {busyAction === "BLOCK" ? "Processing..." : "Block Active Threat"}
        </Button>
        <Button 
          className="w-full" 
          variant="outline"
          onClick={() => handleQuickResponse("ALERT")}
          disabled={busyAction !== null}
        >
          Send Alert
        </Button>
        <Button 
          className="w-full" 
          variant="outline"
          onClick={() => handleQuickResponse("INVESTIGATE")}
          disabled={busyAction !== null}
        >
          Open Investigation
        </Button>
      </CardContent>
    </Card>
  )
}

export function OSProtection() {
  const [protected_status, setProtectedStatus] = useState("HEALTHY")

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-5 h-5" />
          System Status
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <p className="text-sm">Protection Status: <span className={`font-bold ${protected_status === "HEALTHY" ? "text-green-600" : "text-red-600"}`}>
            {protected_status}
          </span></p>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className={`h-2 rounded-full ${protected_status === "HEALTHY" ? "bg-green-600" : "bg-red-600"}`} style={{width: "95%"}}></div>
          </div>
          <p className="text-xs text-slate-600">Last update: Just now</p>
          <Button className="w-full mt-3" size="sm">View Details</Button>
        </div>
      </CardContent>
    </Card>
  )
}
