"use client"

// ===== Consolidated Traffic & Packets =====

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Activity, Network, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { 
  getTrafficByProtocol, 
  getPackets, 
  getPacketStatistics,
  startPacketCapture,
  Packet 
} from "@/lib/api"

export function TrafficPanel() {
  const [trafficData, setTrafficData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchTraffic = async () => {
      try {
        const data: any = await getTrafficByProtocol()
        if (data.protocols) {
          const protocols = Object.entries(data.protocols).map(([name, info]: any) => ({
            protocol: name,
            packets: info.count,
            bytes: (info.bytes / 1024 / 1024).toFixed(2) + " MB",
            percentage: info.percentage
          }))
          setTrafficData(protocols)
        }
        setLoading(false)
      } catch (err) {
        console.error("Failed to fetch traffic:", err)
        setLoading(false)
      }
    }
    
    fetchTraffic()
    const interval = setInterval(fetchTraffic, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Network className="w-5 h-5" />
          Traffic by Protocol
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {loading ? (
            <p className="text-sm text-slate-500">Loading traffic data...</p>
          ) : trafficData.length === 0 ? (
            <p className="text-sm text-slate-500">No traffic data available</p>
          ) : (
            trafficData.map((t: any) => (
              <div key={t.protocol} className="flex justify-between items-center p-2 bg-slate-50 rounded">
                <span className="font-medium">{t.protocol}</span>
                <div className="text-right">
                  <p className="text-sm">{t.packets.toLocaleString()} packets</p>
                  <p className="text-xs text-slate-500">{t.bytes} ({t.percentage}%)</p>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export function TrafficChartPanel() {
  const [stats, setStats] = useState<any>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data: any = await getPacketStatistics()
        setStats(data)
        setLoading(false)
      } catch (err) {
        console.error("Failed to fetch stats:", err)
        setLoading(false)
      }
    }
    
    fetchStats()
    const interval = setInterval(fetchStats, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Network Activity
        </CardTitle>
        <Button size="sm" variant="ghost" onClick={() => window.location.reload()}>
          <RefreshCw className="w-4 h-4" />
        </Button>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="h-48 bg-gradient-to-r from-blue-50 to-blue-100 rounded flex items-center justify-center">
            <p className="text-slate-500">Loading network stats...</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-blue-50 rounded">
                <p className="text-sm text-slate-600">Total Packets</p>
                <p className="text-2xl font-bold text-blue-600">{(stats.total_packets || 0).toLocaleString()}</p>
              </div>
              <div className="p-3 bg-green-50 rounded">
                <p className="text-sm text-slate-600">Total Bytes</p>
                <p className="text-2xl font-bold text-green-600">{((stats.total_bytes || 0) / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              <div className="p-3 bg-purple-50 rounded">
                <p className="text-sm text-slate-600">Avg Packet Size</p>
                <p className="text-2xl font-bold text-purple-600">{(stats.average_packet_size || 0).toFixed(0)} B</p>
              </div>
              <div className="p-3 bg-orange-50 rounded">
                <p className="text-sm text-slate-600">Packets/sec</p>
                <p className="text-2xl font-bold text-orange-600">{(stats.total_packets || 0).toLocaleString()}</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function PacketInspectionPanel() {
  const [packets, setPackets] = useState<Packet[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPackets = async () => {
      try {
        const data = await getPackets(20)
        setPackets(data.packets || [])
        setLoading(false)
      } catch (err) {
        console.error("Failed to fetch packets:", err)
        setLoading(false)
      }
    }
    
    fetchPackets()
    const interval = setInterval(fetchPackets, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Packets</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {loading ? (
            <p className="text-sm text-slate-500">Loading packets...</p>
          ) : packets.length === 0 ? (
            <p className="text-sm text-slate-500">No packets captured yet. Start packet capture to see data.</p>
          ) : (
            packets.slice(0, 10).map((p, i) => (
              <div key={i} className="text-xs p-2 bg-slate-50 rounded border border-slate-200">
                <div className="flex justify-between items-start gap-2">
                  <div>
                    <p className="font-medium">{p.source_ip} → {p.dest_ip}</p>
                    <p className="text-slate-600">{p.protocol}</p>
                  </div>
                  <Badge variant="outline">{p.size_bytes} B</Badge>
                </div>
                {(p.source_port || p.dest_port) && (
                  <p className="text-slate-500 mt-1">
                    Ports: {p.source_port}:{p.dest_port}
                  </p>
                )}
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export function TrafficAnalysisPanel() {
  const [analysis, setAnalysis] = useState<any>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const stats: any = await getPacketStatistics()
        setAnalysis({
          peak_pps: stats.total_packets || 0,
          top_protocol: Object.keys(stats.protocols?.[0] || {})?.[0] || "TCP",
          avg_size: stats.average_packet_size || 0,
          stored_packets: stats.stored_packets || 0
        })
        setLoading(false)
      } catch (err) {
        setLoading(false)
      }
    }
    
    fetchAnalysis()
    const interval = setInterval(fetchAnalysis, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Traffic Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {loading ? (
          <p className="text-sm text-slate-500">Loading analysis...</p>
        ) : (
          <>
            <p className="text-sm">Peak Packets/sec: <Badge>{analysis.peak_pps?.toLocaleString()}</Badge></p>
            <p className="text-sm">Avg Packet Size: <Badge>{analysis.avg_size?.toFixed(0)} B</Badge></p>
            <p className="text-sm">Stored Packets: <Badge>{analysis.stored_packets?.toLocaleString()}</Badge></p>
            <p className="text-sm">Status: <Badge variant="outline" className="bg-green-50 text-green-700">Live Monitoring</Badge></p>
          </>
        )}
      </CardContent>
    </Card>
  )
}
