"""
Consolidated API Routes for ChaosFaction
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# ===== Request/Response Models =====

class TrafficStats(BaseModel):
    timestamp: datetime
    packets_per_second: float
    bytes_per_second: float
    protocol: str

class ThreatData(BaseModel):
    id: str
    type: str
    source_ip: str
    severity: str
    timestamp: datetime
    status: str

class PacketData(BaseModel):
    id: str
    timestamp: datetime
    source_ip: str
    dest_ip: str
    protocol: str
    port: int
    size: int

# ===== TRAFFIC ROUTES =====
traffic_router = APIRouter(prefix="/api/traffic")

@traffic_router.get("/")
async def get_traffic(time_range: str = "hour", protocol: Optional[str] = None):
    """Get network traffic statistics"""
    return {
        "total_packets": 5234,
        "total_bytes": 2500000,
        "packets_per_second": 25.4,
        "protocols": [
            {"name": "TCP", "count": 3500, "bytes": 1800000},
            {"name": "UDP", "count": 1234, "bytes": 600000},
            {"name": "ICMP", "count": 500, "bytes": 100000},
        ]
    }

@traffic_router.get("/history")
async def get_traffic_history(time_range: str = "hour", interval: str = "minute"):
    """Get traffic history for charts"""
    return {
        "data": [
            {"timestamp": "2026-03-01T10:00:00Z", "packets": 50, "bytes": 100000},
            {"timestamp": "2026-03-01T10:01:00Z", "packets": 45, "bytes": 95000},
            {"timestamp": "2026-03-01T10:02:00Z", "packets": 60, "bytes": 120000},
        ]
    }

# ===== THREATS ROUTES =====
threats_router = APIRouter(prefix="/api/threats")

@threats_router.get("/")
async def get_threats(status: str = "active", severity: Optional[str] = None):
    """Get detected threats"""
    return {
        "threats": [
            {
                "id": "threat_001",
                "type": "PORT_SCAN",
                "source_ip": "192.168.1.100",
                "severity": "HIGH",
                "timestamp": "2026-03-01T10:15:30Z",
                "status": "active"
            },
            {
                "id": "threat_002",
                "type": "SUSPICIOUS_TRAFFIC",
                "source_ip": "10.0.0.50",
                "severity": "MEDIUM",
                "timestamp": "2026-03-01T10:10:30Z",
                "status": "active"
            }
        ]
    }

@threats_router.post("/{threat_id}/respond")
async def respond_to_threat(threat_id: str, action: str, reason: Optional[str] = None):
    """Take action on a threat"""
    valid_actions = ["BLOCK", "ALERT", "INVESTIGATE", "IGNORE"]
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of {valid_actions}")
    
    return {
        "success": True,
        "message": f"Threat {threat_id} {action.lower()}ed",
        "action": action
    }

@threats_router.post("/analyze")
async def analyze_for_threats(packet_data: dict):
    """ML-based threat analysis"""
    # Simulated ML prediction
    threat_score = 0.45  # 0-1
    return {
        "is_threat": threat_score > 0.7,
        "threat_type": "NORMAL_TRAFFIC",
        "threat_score": threat_score,
        "recommended_action": "ALLOW"
    }

# ===== PACKETS ROUTES =====
packets_router = APIRouter(prefix="/api/packets")

@packets_router.get("/")
async def get_packets(limit: int = 100, offset: int = 0, filter: Optional[str] = None):
    """Get captured packets"""
    return {
        "packets": [
            {
                "id": "pkt_001",
                "timestamp": "2026-03-01T10:15:30Z",
                "source_ip": "192.168.1.1",
                "dest_ip": "8.8.8.8",
                "protocol": "TCP",
                "length": 1500,
                "port": 443
            }
        ],
        "total": 5234
    }

@packets_router.post("/analyze")
async def analyze_packet(packet_id: str, payload_analysis: bool = False):
    """Deep packet inspection"""
    return {
        "packet_info": {"id": packet_id},
        "payload": "...hex data...",
        "anomalies": [],
        "ml_score": 0.15
    }

@packets_router.post("/capture/start")
async def start_capture(filter: Optional[str] = None, duration: Optional[int] = None):
    """Start packet capture"""
    return {
        "capture_id": "cap_001",
        "status": "started",
        "filter": filter,
        "duration": duration
    }

@packets_router.post("/capture/stop")
async def stop_capture(capture_id: str):
    """Stop packet capture"""
    return {
        "success": True,
        "capture_id": capture_id,
        "packets_captured": 5000
    }

# ===== ADMIN ROUTES =====
admin_router = APIRouter(prefix="/api/admin")

@admin_router.get("/dashboard")
async def admin_dashboard():
    """Admin dashboard overview"""
    return {
        "total_users": 50,
        "total_threats": 1500,
        "system_health": "HEALTHY",
        "uptime_percent": 98.5,
        "last_update": "2026-03-01T10:30:00Z"
    }

@admin_router.get("/settings")
async def get_settings():
    """Get system settings"""
    return {
        "capture_enabled": True,
        "ml_detection_enabled": True,
        "alert_level": "MEDIUM",
        "auto_block": False,
        "backup_enabled": True
    }

@admin_router.put("/settings")
async def update_settings(capture_enabled: Optional[bool] = None, alert_level: Optional[str] = None):
    """Update system settings"""
    return {
        "success": True,
        "message": "Settings updated",
        "capture_enabled": capture_enabled,
        "alert_level": alert_level
    }

@admin_router.get("/users")
async def get_users():
    """Get list of users"""
    return {
        "users": [
            {"id": "user_1", "email": "admin@chaosfaction.com", "role": "admin"},
            {"id": "user_2", "email": "viewer@chaosfaction.com", "role": "viewer"}
        ]
    }

@admin_router.post("/users")
async def create_user(email: str, password: str, role: str):
    """Create new user"""
    if role not in ["admin", "viewer"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    return {
        "success": True,
        "user_id": "user_new",
        "email": email,
        "role": role
    }

@admin_router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Delete user"""
    return {
        "success": True,
        "message": f"User {user_id} deleted"
    }

# ===== NOTIFICATIONS ROUTES =====
notifications_router = APIRouter(prefix="/api/notifications")

@notifications_router.get("/")
async def get_notifications(limit: int = 50):
    """Get notifications"""
    return {
        "notifications": [
            {"id": "notif_1", "type": "THREAT", "message": "High severity threat detected", "read": False},
            {"id": "notif_2", "type": "SYSTEM", "message": "Backup completed", "read": True}
        ]
    }

@notifications_router.post("/{notif_id}/read")
async def mark_notification_read(notif_id: str):
    """Mark notification as read"""
    return {"success": True, "notification_id": notif_id}

@notifications_router.delete("/{notif_id}")
async def delete_notification(notif_id: str):
    """Delete notification"""
    return {"success": True, "notification_id": notif_id}
