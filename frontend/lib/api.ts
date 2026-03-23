// API Utility Functions for ChaosFaction Backend

const DEFAULT_HEADERS = {
  "Content-Type": "application/json",
}

export interface TrafficStats {
  total_packets: number
  total_bytes: number
  average_packet_size: number
  packets_per_second: number
  time_range?: string
  timestamp?: string
}

export interface ProtocolTraffic {
  count: number
  bytes: number
  percentage: number
}

export interface TrafficProtocolResponse {
  protocols: Record<string, ProtocolTraffic>
  total_packets: number
  total_bytes: number
  timestamp: string
}

export interface PacketStatistics {
  total_packets: number
  total_bytes: number
  average_packet_size: number
  protocols: Record<string, number>
  top_ports: Record<string, number>
  stored_packets: number
}

export interface Threat {
  id: string
  type: string
  source_ip: string
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
  threat_score: number
  description: string
  timestamp: string
  status: string
  action_taken?: string
  demo?: boolean
}

export interface Packet {
  timestamp: string
  source_ip: string | null
  dest_ip: string | null
  protocol: string
  application_protocol?: string | null
  source_port?: number | null
  dest_port?: number | null
  size_bytes: number
  flags?: string[]
  dns_query?: string | null
  dns_query_type?: string | null
}

export interface Notification {
  id: string
  type: string
  title: string
  message: string
  severity: string
  timestamp: string
  read: boolean
}

export interface ThreatActionResponse {
  success: boolean
  message: string
  threat_id: string
  action: string
  status: string
}

export interface DemoThreatResponse {
  success: boolean
  scenario: string
  threats_created: number
  threats: Threat[]
}

export interface User {
  id: string
  email: string
  role: "admin" | "viewer"
}

export interface AdminDashboard {
  total_packets: number
  total_threats: number
  critical_threats: number
  system_health: string
  uptime_percent: number
  packet_stats: PacketStatistics
  last_update: string
}

export interface TrafficConnectionsSummary {
  unique_sources: number
  unique_destinations: number
  unique_connections: number
  most_active: Array<{
    connection: string
    packets: number
    bytes: number
  }>
  timestamp: string
}

export interface AdminTrafficSummary {
  summary: TrafficStats
  connections: TrafficConnectionsSummary
  timestamp: string
}

export interface AdminSettings {
  capture_enabled: boolean
  anomaly_detection_enabled: boolean
  alert_level: string
  auto_block: boolean
  backup_enabled: boolean
  pps_threshold: number
  port_scan_threshold: number
}

export interface HealthCheckResponse {
  status: string
  services: Record<string, string>
  timestamp: string
}

class APIError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = "APIError"
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Unknown error" }))
    throw new APIError(response.status, error.detail || "API Error")
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

function buildUrl(path: string, params?: Record<string, string | number | undefined>) {
  const searchParams = new URLSearchParams()

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== "") {
        searchParams.append(key, String(value))
      }
    })
  }

  const query = searchParams.toString()
  return query ? `${path}?${query}` : path
}

async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    cache: "no-store",
    ...init,
    headers: {
      ...DEFAULT_HEADERS,
      ...(init.headers || {}),
    },
  })

  return handleResponse<T>(response)
}

// ===== TRAFFIC ENDPOINTS =====

export async function getTrafficStats(): Promise<TrafficStats> {
  const data = await apiRequest<{ summary?: TrafficStats } & TrafficStats>("/api/traffic")
  return data.summary || data
}

export async function getTrafficByProtocol(): Promise<TrafficProtocolResponse> {
  return apiRequest<TrafficProtocolResponse>("/api/traffic/by-protocol")
}

export async function getTrafficByPort() {
  return apiRequest("/api/traffic/by-port")
}

export async function getTrafficByApplication() {
  return apiRequest("/api/traffic/by-application")
}

export async function getConnectionPatterns() {
  return apiRequest("/api/traffic/connections")
}

export async function getBandwidthPrediction() {
  return apiRequest("/api/traffic/bandwidth-prediction")
}

export async function getTrafficHistory(timeRange = "hour") {
  return apiRequest(buildUrl("/api/traffic/history", { time_range: timeRange }))
}

// ===== THREAT ENDPOINTS =====

export async function getThreats(
  status = "all",
  severity?: string,
): Promise<{ threats: Threat[] }> {
  return apiRequest<{ threats: Threat[] }>(
    buildUrl("/api/threats", { status, severity }),
  )
}

export async function generateDemoThreat(scenario = "random"): Promise<DemoThreatResponse> {
  return apiRequest<DemoThreatResponse>(
    buildUrl("/api/threats/demo", { scenario }),
    {
      method: "POST",
    },
  )
}

export async function analyzeThreatsFull() {
  return apiRequest("/api/threats/analyze", {
    method: "POST",
  })
}

export async function getThreatIntelligence(threatId: string) {
  return apiRequest(`/api/threats/${encodeURIComponent(threatId)}/intelligence`)
}

export async function respondToThreat(threatId: string, action: string): Promise<ThreatActionResponse> {
  return apiRequest<ThreatActionResponse>(
    buildUrl(`/api/threats/${encodeURIComponent(threatId)}/respond`, { action }),
    {
      method: "POST",
    },
  )
}

// ===== PACKET ENDPOINTS =====

export async function getPackets(
  limit = 100,
  offset = 0,
): Promise<{ packets: Packet[] }> {
  return apiRequest<{ packets: Packet[] }>(
    buildUrl("/api/packets", { limit, offset }),
  )
}

export async function filterPackets(filters: {
  source_ip?: string
  dest_ip?: string
  protocol?: string
  port?: number
}) {
  return apiRequest(buildUrl("/api/packets/filter", filters), {
    method: "POST",
  })
}

export async function analyzePackets() {
  return apiRequest("/api/packets/analyze", {
    method: "POST",
  })
}

export async function getPacketStatistics(): Promise<PacketStatistics> {
  return apiRequest<PacketStatistics>("/api/packets/statistics")
}

export async function startPacketCapture(count = 100, timeout = 10) {
  return apiRequest(
    buildUrl("/api/packets/capture/start", { count, timeout }),
    {
      method: "POST",
    },
  )
}

export async function stopPacketCapture() {
  return apiRequest("/api/packets/capture/stop", {
    method: "POST",
  })
}

// ===== ADMIN ENDPOINTS =====

export async function getAdminDashboard(): Promise<AdminDashboard> {
  return apiRequest<AdminDashboard>("/api/admin/dashboard")
}

export async function getAdminSettings(): Promise<AdminSettings> {
  return apiRequest<AdminSettings>("/api/admin/settings")
}

export async function updateAdminSettings(settings: {
  pps_threshold?: number
  port_scan_threshold?: number
  alert_level?: string
}) {
  return apiRequest(buildUrl("/api/admin/settings", settings), {
    method: "PUT",
  })
}

export async function getThreatsSummary() {
  return apiRequest("/api/admin/threats-summary")
}

export async function getThreatssSummary() {
  return getThreatsSummary()
}

export async function getTrafficSummary(): Promise<AdminTrafficSummary> {
  return apiRequest<AdminTrafficSummary>("/api/admin/traffic-summary")
}

// ===== NOTIFICATIONS ENDPOINTS =====

export async function getNotifications(): Promise<{ notifications: Notification[] }> {
  return apiRequest<{ notifications: Notification[] }>("/api/notifications")
}

// ===== USERS ENDPOINTS =====

export async function getUsers(): Promise<{ users: User[] }> {
  return apiRequest<{ users: User[] }>("/api/users")
}

export async function createUser(userData: {
  email: string
  password?: string
  role: User["role"]
}): Promise<User> {
  return apiRequest<User>("/api/users", {
    method: "POST",
    body: JSON.stringify(userData),
  })
}

export async function deleteUser(userId: string) {
  return apiRequest(`/api/users/${encodeURIComponent(userId)}`, {
    method: "DELETE",
  })
}

// ===== HEALTH CHECK =====

export async function healthCheck(): Promise<HealthCheckResponse> {
  return apiRequest<HealthCheckResponse>("/health")
}
