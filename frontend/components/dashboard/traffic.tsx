"use client"

import { useEffect, useState } from "react"
import { Activity, Network, Radar, RefreshCw } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  getPacketStatistics,
  getPackets,
  getTrafficByProtocol,
  getTrafficStats,
  startPacketCapture,
  type Packet,
  type PacketStatistics,
  type StartCaptureResponse,
  type TrafficProtocolResponse,
  type TrafficStats,
} from "@/lib/api"

function formatBytes(bytes: number) {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  }

  if (bytes >= 1024) {
    return `${(bytes / 1024).toFixed(2)} KB`
  }

  return `${bytes} B`
}

function getTopProtocol(protocols: TrafficProtocolResponse["protocols"]) {
  const sortedProtocols = Object.entries(protocols || {}).sort(
    ([, first], [, second]) => second.count - first.count,
  )

  return sortedProtocols[0] || null
}

function getPacketSourceLabel(packet: Packet) {
  if (packet.source_ip) {
    return packet.source_ip
  }

  if (packet.application_protocol === "HTTP_PROXY_HTTP" || packet.application_protocol === "HTTPS_TUNNEL") {
    return "Proxy client"
  }

  return "Captured device"
}

function getPacketDestinationLabel(packet: Packet) {
  if (packet.dest_ip) {
    return packet.dest_ip
  }

  if (packet.observed_host) {
    return packet.observed_host
  }

  if (packet.dns_query) {
    return packet.dns_query
  }

  return "Captured endpoint"
}

export function TrafficPanel() {
  const [trafficData, setTrafficData] = useState<
    Array<{ protocol: string; packets: number; bytes: string; percentage: number }>
  >([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchTraffic = async () => {
      try {
        const data = await getTrafficByProtocol()
        const protocols = Object.entries(data.protocols || {}).map(([name, info]) => ({
          protocol: name,
          packets: info.count,
          bytes: formatBytes(info.bytes),
          percentage: info.percentage,
        }))

        setTrafficData(protocols)
      } catch (error) {
        console.error("Failed to fetch traffic:", error)
      } finally {
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
          <Network className="h-5 w-5" />
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
            trafficData.map((traffic) => (
              <div
                key={traffic.protocol}
                className="flex items-center justify-between rounded bg-slate-50 p-2"
              >
                <span className="font-medium">{traffic.protocol}</span>
                <div className="text-right">
                  <p className="text-sm">{traffic.packets.toLocaleString()} packets</p>
                  <p className="text-xs text-slate-500">
                    {traffic.bytes} ({traffic.percentage}%)
                  </p>
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
  const [summary, setSummary] = useState<TrafficStats | null>(null)
  const [stats, setStats] = useState<PacketStatistics | null>(null)
  const [lastCapture, setLastCapture] = useState<StartCaptureResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [capturing, setCapturing] = useState(false)
  const [error, setError] = useState("")
  const displayedPacketCount = stats?.total_packets ?? lastCapture?.packets_captured ?? 0

  const fetchStats = async () => {
    try {
      const [trafficSummary, packetStats] = await Promise.all([
        getTrafficStats(),
        getPacketStatistics(),
      ])

      setSummary(trafficSummary)
      setStats(packetStats)
      setError("")
    } catch (err) {
      console.error("Failed to fetch stats:", err)
      setError("Unable to reach the backend right now.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleCapture = async () => {
    setCapturing(true)
    setError("")

    try {
      const result = await startPacketCapture(0, 10)
      setLastCapture(result)
      await fetchStats()
      if (result.packets_captured === 0) {
        setError(
          `No packets were captured on interface ${result.interface}. Reload or open the target site during the 10-second capture window.`,
        )
      }
    } catch (err) {
      console.error("Packet capture failed:", err)
      const message =
        err instanceof Error ? err.message : "Packet capture failed. Check backend permissions and try again."

      if (message.includes("/dev/bpf") || message.includes("Scapy as root") || message.includes("admin permissions")) {
        setError(
          "Packet capture needs macOS admin access. Restart using ./scripts/dev-local-capture.sh, or run only the backend with sudo.",
        )
      } else if (message.includes("Npcap") || message.includes("Administrator PowerShell") || message.includes("WinPcap")) {
        setError(
          "Packet capture on Windows needs Npcap and an Administrator PowerShell. Use .\\scripts\\dev-local-capture.ps1 on the Windows machine.",
        )
      } else {
        setError(message)
      }
    } finally {
      setCapturing(false)
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Network Activity
        </CardTitle>
        <div className="flex w-full items-center gap-2 sm:w-auto">
          <Button size="sm" variant="secondary" onClick={handleCapture} disabled={capturing} className="flex-1 sm:flex-none">
            {capturing ? "Capturing..." : "Capture 10s"}
          </Button>
          <Button size="sm" variant="ghost" onClick={fetchStats} className="sm:flex-none">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex h-48 items-center justify-center rounded bg-gradient-to-r from-blue-50 to-blue-100">
            <p className="text-slate-500">Loading network stats...</p>
          </div>
        ) : (
          <div className="space-y-4">
            {error && (
              <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </div>
            )}
            {lastCapture && !error && (
              <div className="rounded border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
                Captured {lastCapture.packets_captured} packet(s) on {lastCapture.interface}.
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              Start capture, then open or hard-reload the target site during the 10-second window.
            </p>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl bg-blue-50 p-4">
                <p className="text-sm text-slate-600">Total Packets</p>
                <p className="text-2xl font-bold text-blue-600">
                  {displayedPacketCount.toLocaleString()}
                </p>
              </div>
              <div className="rounded-2xl bg-green-50 p-4">
                <p className="text-sm text-slate-600">Total Bytes</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatBytes(stats?.total_bytes || 0)}
                </p>
              </div>
              <div className="rounded-2xl bg-purple-50 p-4">
                <p className="text-sm text-slate-600">Avg Packet Size</p>
                <p className="text-2xl font-bold text-purple-600">
                  {(summary?.average_packet_size || stats?.average_packet_size || 0).toFixed(0)} B
                </p>
              </div>
              <div className="rounded-2xl bg-orange-50 p-4">
                <p className="text-sm text-slate-600">Packets/sec</p>
                <p className="text-2xl font-bold text-orange-600">
                  {(summary?.packets_per_second || 0).toLocaleString()}
                </p>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Stored packets: {(stats?.stored_packets || 0).toLocaleString()}
            </p>
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
      } catch (err) {
        console.error("Failed to fetch packets:", err)
      } finally {
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
        <div className="max-h-96 space-y-2 overflow-y-auto">
          {loading ? (
            <p className="text-sm text-slate-500">Loading packets...</p>
          ) : packets.length === 0 ? (
            <p className="text-sm text-slate-500">
              No packets captured yet. Use &quot;Capture 50&quot; to pull live traffic from the backend.
            </p>
          ) : (
            packets.slice(0, 10).map((packet, index) => (
              <div
                key={`${packet.timestamp}-${index}`}
                className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-xs"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium">
                      {getPacketSourceLabel(packet)} → {getPacketDestinationLabel(packet)}
                    </p>
                    <p className="text-slate-600">{packet.protocol}</p>
                  </div>
                  <Badge variant="outline">{packet.size_bytes} B</Badge>
                </div>
                {(packet.source_port || packet.dest_port) && (
                  <p className="mt-1 text-slate-500">
                    Ports: {packet.source_port || "-"}:{packet.dest_port || "-"}
                  </p>
                )}
                {packet.dns_query && (
                  <p className="mt-1 text-slate-500">
                    DNS Query: {packet.dns_query}
                  </p>
                )}
                {packet.observed_host && (
                  <p className="mt-1 text-slate-500">
                    Host Indicator: {packet.observed_host}
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
  const [analysis, setAnalysis] = useState({
    packets_per_second: 0,
    average_packet_size: 0,
    stored_packets: 0,
    top_protocol: "N/A",
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const [summary, stats, protocolData] = await Promise.all([
          getTrafficStats(),
          getPacketStatistics(),
          getTrafficByProtocol(),
        ])

        const topProtocol = getTopProtocol(protocolData.protocols)

        setAnalysis({
          packets_per_second: summary.packets_per_second || 0,
          average_packet_size: summary.average_packet_size || stats.average_packet_size || 0,
          stored_packets: stats.stored_packets || 0,
          top_protocol: topProtocol?.[0] || "N/A",
        })
      } catch (err) {
        console.error("Failed to fetch traffic analysis:", err)
      } finally {
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
        <CardTitle className="flex items-center gap-2">
          <Radar className="h-5 w-5" />
          Traffic Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {loading ? (
          <p className="text-sm text-slate-500">Loading analysis...</p>
        ) : (
          <>
            <p className="text-sm">
              Current Packets/sec: <Badge>{analysis.packets_per_second.toLocaleString()}</Badge>
            </p>
            <p className="text-sm">
              Avg Packet Size: <Badge>{analysis.average_packet_size.toFixed(0)} B</Badge>
            </p>
            <p className="text-sm">
              Stored Packets: <Badge>{analysis.stored_packets.toLocaleString()}</Badge>
            </p>
            <p className="text-sm">
              Top Protocol: <Badge variant="outline">{analysis.top_protocol}</Badge>
            </p>
            <p className="text-sm">
              Status:{" "}
              <Badge variant="outline" className="bg-green-50 text-green-700">
                Live Monitoring
              </Badge>
            </p>
          </>
        )}
      </CardContent>
    </Card>
  )
}
