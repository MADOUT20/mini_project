"use client"

// ===== Consolidated Threats =====

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AlertTriangle, Shield, Zap } from "lucide-react"

export function ThreatDetectionPanel() {
  const threats = [
    { id: 1, name: "Port Scan Detected", severity: "HIGH", ip: "192.168.1.100" },
    { id: 2, name: "Unusual Traffic Pattern", severity: "MEDIUM", ip: "10.0.0.50" },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-500" />
          Threats Detected
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {threats.map(threat => (
          <div key={threat.id} className="p-3 bg-red-50 border border-red-200 rounded">
            <div className="flex justify-between items-start mb-2">
              <p className="font-medium">{threat.name}</p>
              <Badge variant="destructive">{threat.severity}</Badge>
            </div>
            <p className="text-sm text-slate-600 mb-3">Source: {threat.ip}</p>
            <div className="flex gap-2">
              <Button size="sm" className="bg-red-600 hover:bg-red-700">Block</Button>
              <Button size="sm" variant="outline">Investigate</Button>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export function ThreatResponsePanel() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="w-5 h-5" />
          Quick Actions
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <Button className="w-full" variant="outline">Block Threat</Button>
        <Button className="w-full" variant="outline">Quarantine</Button>
        <Button className="w-full" variant="outline">Generate Report</Button>
      </CardContent>
    </Card>
  )
}

export function OSProtection() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-5 h-5" />
          OS Protection
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <p className="text-sm">Status: <span className="font-bold text-green-600">Protected</span></p>
          <p className="text-sm">Last Update: <span className="text-slate-600">2 hours ago</span></p>
          <Button className="w-full mt-3" size="sm">Update Now</Button>
        </div>
      </CardContent>
    </Card>
  )
}
