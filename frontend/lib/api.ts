// API Utility Functions for ChaosFaction Backend

// @ts-ignore
const API_URL = process?.env?.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// ===== Type Definitions =====

export interface TrafficStats {
  total_packets: number;
  total_bytes: number;
  average_packet_size: number;
  packets_per_second: number;
  timestamp: string;
}

export interface Threat {
  id: string;
  type: string;
  source_ip: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  threat_score: number;
  description: string;
  timestamp: string;
  status: string;
}

export interface Packet {
  timestamp: string;
  source_ip: string;
  dest_ip: string;
  protocol: string;
  source_port?: number;
  dest_port?: number;
  size_bytes: number;
  flags?: string[];
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  severity: string;
  timestamp: string;
  read: boolean;
}

// ===== Error Handling =====

class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "APIError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new APIError(response.status, error.detail || "API Error");
  }
  return response.json();
}

// ===== TRAFFIC ENDPOINTS =====

export async function getTrafficStats(): Promise<TrafficStats> {
  try {
    const response = await fetch(`${API_URL}/api/traffic/`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    const data = await handleResponse<any>(response);
    return data.summary || data;
  } catch (error) {
    console.error("Failed to fetch traffic stats:", error);
    throw error;
  }
}

export async function getTrafficByProtocol() {
  try {
    const response = await fetch(`${API_URL}/api/traffic/by-protocol`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to fetch protocol stats:", error);
    throw error;
  }
}

export async function getTrafficByPort() {
  try {
    const response = await fetch(`${API_URL}/api/traffic/by-port`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to fetch port stats:", error);
    throw error;
  }
}

export async function getTrafficByApplication() {
  try {
    const response = await fetch(`${API_URL}/api/traffic/by-application`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to fetch application stats:", error);
    throw error;
  }
}

export async function getConnectionPatterns() {
  try {
    const response = await fetch(`${API_URL}/api/traffic/connections`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to fetch connection patterns:", error);
    throw error;
  }
}

export async function getBandwidthPrediction() {
  try {
    const response = await fetch(`${API_URL}/api/traffic/bandwidth-prediction`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to fetch bandwidth prediction:", error);
    throw error;
  }
}

export async function getTrafficHistory(timeRange: string = "hour") {
  try {
    const response = await fetch(`${API_URL}/api/traffic/history?time_range=${timeRange}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to fetch traffic history:", error);
    throw error;
  }
}

// ===== THREAT ENDPOINTS =====

export async function getThreats(status: string = "active", severity?: string): Promise<{ threats: Threat[] }> {
  try {
    let url = `${API_URL}/api/threats/?status=${status}`;
    if (severity) url += `&severity=${severity}`;
    
    const response = await fetch(url, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to fetch threats:", error);
    throw error;
  }
}

export async function analyzeThreatsFull() {
  try {
    const response = await fetch(`${API_URL}/api/threats/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to analyze threats:", error);
    throw error;
  }
}

export async function getThreatIntelligence(threatId: string) {
  try {
    const response = await fetch(`${API_URL}/api/threats/${threatId}/intelligence`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to fetch threat intelligence:", error);
    throw error;
  }
}

export async function respondToThreat(threatId: string, action: string) {
  try {
    const response = await fetch(
      `${API_URL}/api/threats/${threatId}/respond?action=${action}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      }
    );
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to respond to threat:", error);
    throw error;
  }
}

// ===== PACKET ENDPOINTS =====

export async function getPackets(limit: number = 100, offset: number = 0): Promise<{ packets: Packet[] }> {
  try {
    const response = await fetch(`${API_URL}/api/packets/?limit=${limit}&offset=${offset}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to fetch packets:", error);
    throw error;
  }
}

export async function filterPackets(filters: {
  source_ip?: string;
  dest_ip?: string;
  protocol?: string;
  port?: number;
}) {
  try {
    const params = new URLSearchParams();
    if (filters.source_ip) params.append("source_ip", filters.source_ip);
    if (filters.dest_ip) params.append("dest_ip", filters.dest_ip);
    if (filters.protocol) params.append("protocol", filters.protocol);
    if (filters.port) params.append("port", filters.port.toString());

    const response = await fetch(`${API_URL}/api/packets/filter?${params}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to filter packets:", error);
    throw error;
  }
}

export async function analyzePackets() {
  try {
    const response = await fetch(`${API_URL}/api/packets/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to analyze packets:", error);
    throw error;
  }
}

export async function getPacketStatistics() {
  try {
    const response = await fetch(`${API_URL}/api/packets/statistics`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to get packet statistics:", error);
    throw error;
  }
}

export async function startPacketCapture(count: number = 100, timeout: number = 10) {
  try {
    const response = await fetch(
      `${API_URL}/api/packets/capture/start?count=${count}&timeout=${timeout}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      }
    );
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to start packet capture:", error);
    throw error;
  }
}

export async function stopPacketCapture() {
  try {
    const response = await fetch(`${API_URL}/api/packets/capture/stop`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to stop packet capture:", error);
    throw error;
  }
}

// ===== ADMIN ENDPOINTS =====

export async function getAdminDashboard() {
  try {
    const response = await fetch(`${API_URL}/api/admin/dashboard`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to fetch admin dashboard:", error);
    throw error;
  }
}

export async function getAdminSettings() {
  try {
    const response = await fetch(`${API_URL}/api/admin/settings`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to fetch admin settings:", error);
    throw error;
  }
}

export async function updateAdminSettings(settings: {
  pps_threshold?: number;
  port_scan_threshold?: number;
  alert_level?: string;
}) {
  try {
    const params = new URLSearchParams();
    if (settings.pps_threshold) params.append("pps_threshold", settings.pps_threshold.toString());
    if (settings.port_scan_threshold) params.append("port_scan_threshold", settings.port_scan_threshold.toString());
    if (settings.alert_level) params.append("alert_level", settings.alert_level);

    const response = await fetch(`${API_URL}/api/admin/settings?${params}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to update admin settings:", error);
    throw error;
  }
}

export async function getThreatssSummary() {
  try {
    const response = await fetch(`${API_URL}/api/admin/threats-summary`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to fetch threats summary:", error);
    throw error;
  }
}

export async function getTrafficSummary() {
  try {
    const response = await fetch(`${API_URL}/api/admin/traffic-summary`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to fetch traffic summary:", error);
    throw error;
  }
}

// ===== NOTIFICATIONS ENDPOINTS =====

export async function getNotifications(): Promise<{ notifications: Notification[] }> {
  try {
    const response = await fetch(`${API_URL}/api/notifications/`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Failed to fetch notifications:", error);
    throw error;
  }
}

// ===== HEALTH CHECK =====

export async function healthCheck() {
  try {
    const response = await fetch(`${API_URL}/health`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse(response);
  } catch (error) {
    console.error("Health check failed:", error);
    throw error;
  }
}
