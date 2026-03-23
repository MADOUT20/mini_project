"use client"

// ===== Consolidated Threats =====

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AlertTriangle, Shield, Zap, RefreshCw } from "lucide-react"
import { generateDemoThreat, getThreats, respondToThreat, Threat } from "@/lib/api"

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

export function ThreatDetectionPanel() {
  const [threats, setThreats] = useState<Threat[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

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
    } catch (err) {
      setMessage("Failed to respond to threat")
    }
  }

  const visibleThreats = threats.slice(0, 5)

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
          Threats Detected ({threats.length})
        </CardTitle>
        <Button size="sm" variant="ghost" onClick={fetchThreats}>
          <RefreshCw className="w-4 h-4" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {error && <div className="text-red-500 text-sm">{error}</div>}
        {message && <div className="text-sm text-slate-600">{message}</div>}
        
        {threats.length === 0 ? (
          <div className="p-3 bg-green-50 border border-green-200 rounded text-center">
            <p className="text-sm font-medium text-green-700">No threats detected</p>
            <p className="text-xs text-green-600">Network is secure</p>
          </div>
        ) : (
          visibleThreats.map((threat) => (
            <div key={threat.id} className={`p-3 border rounded ${getSeverityClass(threat.severity)}`}>
              <div className="flex justify-between items-start mb-2">
                <div>
                  <p className="font-medium text-sm">{threat.type}</p>
                  <p className="text-xs text-slate-600">Source: {threat.source_ip}</p>
                </div>
                <div className="flex flex-wrap justify-end gap-2">
                  <Badge
                    variant={threat.severity === "CRITICAL" ? "destructive" : "default"}
                    className={
                      threat.severity === "HIGH"
                        ? "bg-orange-600"
                        : threat.severity === "MEDIUM"
                          ? "bg-yellow-600"
                          : "bg-blue-600"
                    }
                  >
                    {threat.severity}
                  </Badge>
                  <Badge variant="outline">{formatStatus(threat.status)}</Badge>
                  {threat.demo && <Badge variant="secondary">Demo</Badge>}
                </div>
              </div>
              <p className="text-xs text-slate-600 mb-2">{threat.description}</p>
              <p className="text-xs text-slate-500 mb-2">Confidence: {(threat.threat_score * 100).toFixed(0)}%</p>
              <div className="flex gap-2">
                <Button 
                  size="sm" 
                  className="bg-red-600 hover:bg-red-700 text-xs"
                  onClick={() => handleThreatAction(threat.id, "BLOCK")}
                  disabled={threat.status === "blocked"}
                >
                  {threat.status === "blocked" ? "Blocked" : "Block"}
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  className="text-xs"
                  onClick={() => handleThreatAction(threat.id, "INVESTIGATE")}
                >
                  Investigate
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

  const handleGenerateDemo = async (scenario: string) => {
    setBusyAction(`demo-${scenario}`)
    try {
      const result = await generateDemoThreat(scenario)
      const label = scenario === "all" ? "demo threat pack" : "demo threat"
      setMessage(result.success ? `Generated ${label} successfully` : `Failed to generate ${label}`)
      emitDashboardRefresh()
    } catch (err) {
      setMessage("Failed to generate demo threats")
    }
    setBusyAction(null)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="w-5 h-5" />
          Quick Response
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-xs text-slate-500">
          Demo actions only update the dashboard state. They do not change your real firewall.
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
        <Button
          className="w-full"
          variant="secondary"
          onClick={() => handleGenerateDemo("random")}
          disabled={busyAction !== null}
        >
          {busyAction === "demo-random" ? "Generating..." : "Generate Demo Threat"}
        </Button>
        <Button
          className="w-full"
          variant="outline"
          onClick={() => handleGenerateDemo("all")}
          disabled={busyAction !== null}
        >
          {busyAction === "demo-all" ? "Generating..." : "Generate Demo Threat Pack"}
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
