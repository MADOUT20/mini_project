"use client"

// ===== Consolidated Threats =====

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AlertTriangle, Shield, Zap, RefreshCw } from "lucide-react"
import { getThreats, respondToThreat, Threat } from "@/lib/api"

export function ThreatDetectionPanel() {
  const [threats, setThreats] = useState<Threat[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const fetchThreats = async () => {
    try {
      setLoading(true)
      const data = await getThreats("active")
      setThreats(data.threats || [])
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
    // Refresh every 5 seconds
    const interval = setInterval(fetchThreats, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleThreatAction = async (threatId: string, action: string) => {
    try {
      await respondToThreat(threatId, action)
      alert(`Threat ${action.toLowerCase()}ed successfully!`)
      fetchThreats()
    } catch (err) {
      alert("Failed to respond to threat")
    }
  }

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
        
        {threats.length === 0 ? (
          <div className="p-3 bg-green-50 border border-green-200 rounded text-center">
            <p className="text-sm font-medium text-green-700">✅ No threats detected</p>
            <p className="text-xs text-green-600">Network is secure</p>
          </div>
        ) : (
          threats.slice(0, 3).map((threat) => (
            <div key={threat.id} className={`p-3 border rounded ${
              threat.severity === "CRITICAL" ? "bg-red-50 border-red-200" :
              threat.severity === "HIGH" ? "bg-orange-50 border-orange-200" :
              threat.severity === "MEDIUM" ? "bg-yellow-50 border-yellow-200" :
              "bg-blue-50 border-blue-200"
            }`}>
              <div className="flex justify-between items-start mb-2">
                <div>
                  <p className="font-medium text-sm">{threat.type}</p>
                  <p className="text-xs text-slate-600">Source: {threat.source_ip}</p>
                </div>
                <Badge 
                  variant={threat.severity === "CRITICAL" ? "destructive" : "default"}
                  className={
                    threat.severity === "HIGH" ? "bg-orange-600" :
                    threat.severity === "MEDIUM" ? "bg-yellow-600" :
                    "bg-blue-600"
                  }
                >
                  {threat.severity}
                </Badge>
              </div>
              <p className="text-xs text-slate-600 mb-2">{threat.description}</p>
              <p className="text-xs text-slate-500 mb-2">Confidence: {(threat.threat_score * 100).toFixed(0)}%</p>
              <div className="flex gap-2">
                <Button 
                  size="sm" 
                  className="bg-red-600 hover:bg-red-700 text-xs"
                  onClick={() => handleThreatAction(threat.id, "BLOCK")}
                >
                  Block
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
  const [responding, setResponding] = useState(false)

  const handleQuickResponse = async (action: string) => {
    setResponding(true)
    try {
      const data = await getThreats("active")
      const threats = data.threats || []
      
      if (threats.length > 0) {
        const threat = threats[0]
        await respondToThreat(threat.id, action)
        alert(`Quick action '${action}' executed!`)
      } else {
        alert("No active threats to respond to")
      }
    } catch (err) {
      alert("Failed to execute action")
    }
    setResponding(false)
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
        <Button 
          className="w-full" 
          onClick={() => handleQuickResponse("BLOCK")}
          disabled={responding}
        >
          {responding ? "Processing..." : "Block Active Threat"}
        </Button>
        <Button 
          className="w-full" 
          variant="outline"
          onClick={() => handleQuickResponse("ALERT")}
          disabled={responding}
        >
          Send Alert
        </Button>
        <Button 
          className="w-full" 
          variant="outline"
          onClick={() => handleQuickResponse("INVESTIGATE")}
          disabled={responding}
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
