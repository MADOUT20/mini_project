"use client"

// ===== Consolidated Traffic & Packets =====

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Activity, Network } from "lucide-react"

export function TrafficPanel() {
  const trafficData = [
    { protocol: "TCP", packets: 5234, bytes: "2.5 MB" },
    { protocol: "UDP", packets: 1823, bytes: "850 KB" },
    { protocol: "ICMP", packets: 342, bytes: "125 KB" },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Network className="w-5 h-5" />
          Traffic Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {trafficData.map((t: any) => (
            <div key={t.protocol} className="flex justify-between items-center p-2 bg-slate-50 rounded">
              <span className="font-medium">{t.protocol}</span>
              <div className="text-right">
                <p className="text-sm">{t.packets} packets</p>
                <p className="text-xs text-slate-500">{t.bytes}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export function TrafficChartPanel() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Network Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-48 bg-gradient-to-r from-blue-50 to-blue-100 rounded flex items-center justify-center">
          <p className="text-slate-500">Chart visualization (connect to real data)</p>
        </div>
      </CardContent>
    </Card>
  )
}

export function PacketInspectionPanel() {
  const packets = [
    { id: 1, src: "192.168.1.1", dst: "8.8.8.8", proto: "TCP", size: "1500B" },
    { id: 2, src: "10.0.0.5", dst: "1.1.1.1", proto: "UDP", size: "512B" },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Packets</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {packets.map((p: any) => (
            <div key={p.id} className="text-xs p-2 bg-slate-50 rounded">
              <p>{p.src} → {p.dst} | {p.proto}</p>
              <p className="text-slate-500">{p.size}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export function TrafficAnalysisPanel() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Traffic Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-sm">Peak Time: <Badge>14:30 - 15:00</Badge></p>
        <p className="text-sm">Avg Packets/sec: <Badge>152.4</Badge></p>
        <p className="text-sm">Top Protocol: <Badge>TCP (72%)</Badge></p>
      </CardContent>
    </Card>
  )
}
