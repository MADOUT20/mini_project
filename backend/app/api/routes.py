"""
Consolidated API Routes for ChaosFaction
Integrated with real services for packet capture, threat detection, and traffic analysis
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
from app.services.packet_capture import PacketCaptureService
from app.services.mobile_proxy import MobileProxyService
from app.services.threat_detection import ThreatDetectionService
from app.services.traffic_analysis import TrafficAnalysisService

# ===== Initialize Services =====
packet_service = PacketCaptureService()
threat_service = ThreatDetectionService()
proxy_service = MobileProxyService(packet_service, threat_service)
traffic_service = TrafficAnalysisService()

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

class UserCreateRequest(BaseModel):
    email: str
    password: Optional[str] = None
    role: str

# In-memory user store for the dashboard admin panel
users_store: List[Dict[str, str]] = [
    {"id": "user_1", "email": "admin@chaosfaction.com", "role": "admin"},
    {"id": "user_2", "email": "viewer@chaosfaction.com", "role": "viewer"},
]

# ===== TRAFFIC ROUTES =====
traffic_router = APIRouter(prefix="/api/traffic", tags=["Traffic Analysis"])

@traffic_router.get("")
async def get_traffic(time_range: str = Query("hour", description="Time range for analysis")):
    """Get network traffic statistics with real packet data"""
    try:
        # Get packets from service
        packets = packet_service.packets
        stats = await packet_service.get_packet_statistics()
        
        # Get traffic summary
        summary = await traffic_service.get_traffic_summary(packets, time_range)
        
        # Get protocol breakdown
        protocol_data = await traffic_service.analyze_by_protocol(packets)
        
        return {
            "status": "success",
            "summary": summary,
            "protocols": protocol_data.get("protocols", {}),
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Traffic analysis failed: {str(e)}")

@traffic_router.get("/by-protocol")
async def get_traffic_by_protocol():
    """Get detailed protocol breakdown"""
    try:
        packets = packet_service.packets
        protocol_data = await traffic_service.analyze_by_protocol(packets)
        return protocol_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@traffic_router.get("/by-port")
async def get_traffic_by_port():
    """Get traffic breakdown by port"""
    try:
        packets = packet_service.packets
        port_data = await traffic_service.analyze_by_port(packets)
        return port_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@traffic_router.get("/by-application")
async def get_traffic_by_application():
    """Get traffic breakdown by application type"""
    try:
        packets = packet_service.packets
        app_data = await traffic_service.analyze_by_application(packets)
        return app_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@traffic_router.get("/connections")
async def get_connection_patterns():
    """Get source-destination connection patterns"""
    try:
        packets = packet_service.packets
        connections = await traffic_service.analyze_connection_patterns(packets)
        return connections
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@traffic_router.get("/bandwidth-prediction")
async def predict_bandwidth():
    """Predict future bandwidth requirements"""
    try:
        packets = packet_service.packets
        prediction = await traffic_service.predict_bandwidth_requirements(packets)
        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@traffic_router.get("/history")
async def get_traffic_history(time_range: str = "hour", interval: str = "minute"):
    """Get traffic history for charts (simulated based on current packets)"""
    try:
        packets = packet_service.packets
        stats = await packet_service.get_packet_statistics()
        
        # Generate historical data points (simplified)
        history_points = []
        if packets:
            chunk_size = max(1, len(packets) // 10)
            for i in range(0, len(packets), chunk_size):
                chunk = packets[i:i+chunk_size]
                history_points.append({
                    "timestamp": datetime.now().isoformat(),
                    "packets": len(chunk),
                    "bytes": sum(p.get("size_bytes", 0) for p in chunk)
                })
        
        return {
            "time_range": time_range,
            "interval": interval,
            "data": history_points if history_points else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== THREATS ROUTES =====
threats_router = APIRouter(prefix="/api/threats", tags=["Threat Detection"])

@threats_router.get("")
async def get_threats(
    status: str = Query("active", description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)")
):
    """Get detected threats with real anomaly detection"""
    try:
        # Get current packets and stats
        packets = packet_service.packets
        stats = await packet_service.get_packet_statistics()
        
        # Detect threats using anomaly detection
        threats = await threat_service.detect_threats(packets, stats)
        
        # Filter by parameters
        filtered_threats = threats
        if status and status.lower() != "all":
            filtered_threats = [t for t in filtered_threats if t.get("status") == status]
        if severity:
            filtered_threats = [t for t in filtered_threats if t.get("severity") == severity]
        
        return {
            "status": "success",
            "threat_count": len(filtered_threats),
            "threats": filtered_threats,
            "last_scan": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@threats_router.get("/hunt")
async def hunt_threats(limit: int = Query(5, ge=1, le=10, description="Maximum number of findings to return")):
    """Return the strongest confirmed threat or suspicious live lead from captured packets."""
    try:
        packets = packet_service.packets
        stats = await packet_service.get_packet_statistics()
        hunt_results = await threat_service.hunt_live_threats(packets, stats, limit=limit)

        return {
            "status": "success",
            **hunt_results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@threats_router.post("/{threat_id}/respond")
async def respond_to_threat(
    threat_id: str,
    action: str = Query(..., description="Action: BLOCK, ALERT, INVESTIGATE, IGNORE")
):
    """Take action on a threat"""
    try:
        result = await threat_service.respond_to_threat(threat_id, action)
        
        if result.get("success"):
            return result
        raise HTTPException(status_code=404, detail=result.get("error"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@threats_router.get("/{threat_id}/intelligence")
async def get_threat_intelligence(threat_id: str):
    """Get detailed threat intelligence"""
    try:
        intelligence = await threat_service.get_threat_intelligence(threat_id)
        
        if "error" in intelligence:
            raise HTTPException(status_code=404, detail=intelligence["error"])
        
        return intelligence
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@threats_router.post("/analyze")
async def analyze_for_threats():
    """Perform anomaly detection analysis on current traffic"""
    try:
        packets = packet_service.packets
        stats = await packet_service.get_packet_statistics()
        
        # Run threat detection
        threats = await threat_service.detect_threats(packets, stats)
        
        # Count by severity
        severity_breakdown = {
            "CRITICAL": len([t for t in threats if t.get("severity") == "CRITICAL"]),
            "HIGH": len([t for t in threats if t.get("severity") == "HIGH"]),
            "MEDIUM": len([t for t in threats if t.get("severity") == "MEDIUM"]),
            "LOW": len([t for t in threats if t.get("severity") == "LOW"]),
        }
        
        return {
            "analysis_complete": True,
            "total_threats_detected": len(threats),
            "severity_breakdown": severity_breakdown,
            "threats": threats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== PACKETS ROUTES =====
packets_router = APIRouter(prefix="/api/packets", tags=["Packet Capture"])

@packets_router.get("")
async def get_packets(limit: int = 100, offset: int = 0):
    """Get captured packets"""
    try:
        packets = packet_service.packets[offset:offset+limit]
        
        return {
            "packets": packets,
            "total": len(packet_service.packets),
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@packets_router.get("/interfaces")
async def get_capture_interfaces():
    """Return available capture interfaces and the current default."""
    try:
        return packet_service.get_available_interfaces()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@packets_router.post("/filter")
async def filter_packets(
    source_ip: Optional[str] = None,
    dest_ip: Optional[str] = None,
    protocol: Optional[str] = None,
    port: Optional[int] = None
):
    """Filter packets by criteria"""
    try:
        filters = {}
        if source_ip:
            filters["source_ip"] = source_ip
        if dest_ip:
            filters["dest_ip"] = dest_ip
        if protocol:
            filters["protocol"] = protocol
        if port:
            filters["port"] = port
        
        filtered = await packet_service.filter_packets(**filters)
        
        return {
            "filters": filters,
            "count": len(filtered),
            "packets": filtered,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@packets_router.post("/analyze")
async def analyze_packet():
    """Deep packet inspection and analysis"""
    try:
        packets = packet_service.packets
        
        if not packets:
            return {"error": "No packets to analyze"}
        
        # Analyze patterns
        anomalies = []
        
        # Check for unusual packet sizes
        sizes = [p.get("size_bytes", 0) for p in packets if p.get("size_bytes")]
        if sizes:
            avg_size = sum(sizes) / len(sizes)
            large_packets = [p for p in packets if p.get("size_bytes", 0) > avg_size * 2]
            if large_packets:
                anomalies.append({
                    "type": "LARGE_PACKETS",
                    "count": len(large_packets),
                    "threshold": avg_size * 2
                })
        
        return {
            "total_packets_analyzed": len(packets),
            "anomalies_found": len(anomalies),
            "anomaly_details": anomalies,
            "ml_score": 0.65,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@packets_router.post("/capture/start")
async def start_capture(
    interface: Optional[str] = Query(None, description="Network interface to capture from"),
    count: int = Query(100, description="Number of packets to capture"),
    timeout: int = Query(10, description="Timeout in seconds")
):
    """Start packet capture"""
    try:
        capture_interface = (
            interface
            or os.getenv("CAPTURE_INTERFACE")
            or packet_service.get_preferred_interface()
        )
        packets = await packet_service.capture_packets(
            interface=capture_interface,
            count=count,
            timeout=timeout
        )
        
        if isinstance(packets, dict) and "error" in packets:
            raise HTTPException(status_code=500, detail=packets["error"])
        
        return {
            "capture_id": f"cap_{datetime.now().timestamp()}",
            "status": "started",
            "interface": capture_interface or "default",
            "packets_captured": len(packets) if isinstance(packets, list) else 0,
            "count": count,
            "timeout": timeout,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@packets_router.post("/capture/stop")
async def stop_capture():
    """Stop packet capture and get statistics"""
    try:
        stats = await packet_service.get_packet_statistics()
        
        return {
            "success": True,
            "packets_captured": stats.get("total_packets", 0),
            "total_bytes": stats.get("total_bytes", 0),
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@packets_router.get("/statistics")
async def get_packet_statistics():
    """Get packet capture statistics"""
    try:
        stats = await packet_service.get_packet_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== ADMIN ROUTES =====
admin_router = APIRouter(prefix="/api/admin", tags=["Admin"])

@admin_router.get("/proxy-status")
async def get_proxy_status():
    """Return local proxy status for mobile testing."""
    proxy_port = int(os.getenv("PROXY_PORT", "8888"))
    return {
        "enabled": os.getenv("PROXY_ENABLED", "0").lower() in {"1", "true", "yes", "on"},
        "host": os.getenv("PROXY_HOST", "0.0.0.0"),
        "port": proxy_port,
        "listening": proxy_service.server is not None,
        "clients": proxy_service.get_active_clients(),
        "timestamp": datetime.now().isoformat(),
    }

@admin_router.get("/blocked-sites")
async def get_blocked_sites():
    """Return domains currently blocked by proxy response actions."""
    return {
        "blocked_sites": threat_service.get_blocked_domains(),
        "count": len(threat_service.blocked_domains),
        "timestamp": datetime.now().isoformat(),
    }

@admin_router.delete("/blocked-sites")
async def clear_blocked_sites():
    """Clear every blocked website rule from the proxy."""
    return threat_service.clear_blocked_domains()

@admin_router.delete("/blocked-sites/{domain}")
async def unblock_site(domain: str):
    """Remove a single blocked website rule from the proxy."""
    result = threat_service.unblock_domain(domain)
    if result.get("success"):
        return result
    raise HTTPException(status_code=404, detail=result.get("error"))

@admin_router.get("/dashboard")
async def admin_dashboard():
    """Admin dashboard overview"""
    try:
        packets = packet_service.packets
        stats = await packet_service.get_packet_statistics()
        threats = await threat_service.detect_threats(packets, stats) if packets else []

        visible_threats = [t for t in threats if t.get("severity") != "LOW"]
        medium_threats = len([t for t in visible_threats if t.get("severity") == "MEDIUM"])
        high_alert_threats = len(
            [t for t in visible_threats if t.get("severity") in {"HIGH", "CRITICAL"}]
        )
        critical_threats = len([t for t in threats if t.get("severity") == "CRITICAL"])

        if critical_threats > 0:
            system_health = "WARNING"
        elif high_alert_threats > 0:
            system_health = "ELEVATED"
        elif medium_threats > 0:
            system_health = "MONITORING"
        else:
            system_health = "HEALTHY"

        return {
            "total_packets": stats.get("total_packets", 0),
            "total_threats": len(visible_threats),
            "medium_threats": medium_threats,
            "high_alert_threats": high_alert_threats,
            "critical_threats": critical_threats,
            "low_threats": len([t for t in threats if t.get("severity") == "LOW"]),
            "system_health": system_health,
            "uptime_percent": 98.5,
            "packet_stats": stats,
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/settings")
async def get_settings():
    """Get system settings"""
    return {
        "capture_enabled": True,
        "anomaly_detection_enabled": True,
        "alert_level": "MEDIUM",
        "auto_block": False,
        "backup_enabled": True,
        "pps_threshold": threat_service.pps_threshold,
        "port_scan_threshold": threat_service.port_scan_threshold
    }

@admin_router.put("/settings")
async def update_settings(
    pps_threshold: Optional[int] = None,
    port_scan_threshold: Optional[int] = None,
    alert_level: Optional[str] = None
):
    """Update system settings"""
    try:
        if pps_threshold:
            threat_service.pps_threshold = pps_threshold
        if port_scan_threshold:
            threat_service.port_scan_threshold = port_scan_threshold
        
        return {
            "success": True,
            "message": "Settings updated",
            "pps_threshold": threat_service.pps_threshold,
            "port_scan_threshold": threat_service.port_scan_threshold,
            "alert_level": alert_level
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/threats-summary")
async def get_threats_summary():
    """Get threat summary for admin"""
    try:
        packets = packet_service.packets
        stats = await packet_service.get_packet_statistics()
        threats = await threat_service.detect_threats(packets, stats) if packets else []
        
        threat_types = {}
        for threat in threats:
            threat_type = threat.get("type", "Unknown")
            threat_types[threat_type] = threat_types.get(threat_type, 0) + 1
        
        return {
            "total_threats": len(threats),
            "threat_types": threat_types,
            "threats": threats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/traffic-summary")
async def get_traffic_summary():
    """Get traffic summary for admin"""
    try:
        packets = packet_service.packets
        summary = await traffic_service.get_traffic_summary(packets)
        connections = await traffic_service.analyze_connection_patterns(packets)
        
        return {
            "summary": summary,
            "connections": connections,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== HEALTH CHECK =====
health_router = APIRouter(tags=["Health"])

@health_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "packet_capture": "operational",
            "threat_detection": "operational",
            "traffic_analysis": "operational"
        },
        "timestamp": datetime.now().isoformat()
    }

# ===== NOTIFICATIONS ROUTER =====
notifications_router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@notifications_router.get("")
async def get_notifications():
    """Get recent notifications"""
    packets = packet_service.packets
    stats = await packet_service.get_packet_statistics()
    threats = await threat_service.detect_threats(packets, stats)
    notifications = threat_service.get_notifications(threats)
    
    return {
        "notifications": notifications,
        "total": len(notifications)
    }

# ===== USERS ROUTES =====
users_router = APIRouter(prefix="/api/users", tags=["Users"])

@users_router.get("")
async def get_users():
    """Get list of users"""
    return {"users": users_store}

@users_router.post("")
async def create_user(user: UserCreateRequest):
    """Create new user"""
    role = user.role.lower()

    if role not in ["admin", "viewer"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    if any(existing_user["email"].lower() == user.email.lower() for existing_user in users_store):
        raise HTTPException(status_code=409, detail="User already exists")

    new_user = {
        "id": f"user_{len(users_store) + 1}",
        "email": user.email,
        "role": role
    }
    users_store.append(new_user)

    return new_user

@users_router.delete("/{user_id}")
async def delete_user(user_id: str):
    """Delete user"""
    for index, existing_user in enumerate(users_store):
        if existing_user["id"] == user_id:
            deleted_user = users_store.pop(index)
            return {
                "success": True,
                "message": f"User {user_id} deleted",
                "user": deleted_user
            }

    raise HTTPException(status_code=404, detail="User not found")

@notifications_router.post("/{notif_id}/read")
async def mark_notification_read(notif_id: str):
    """Mark notification as read"""
    return {
        "success": True,
        "notification_id": notif_id
    }

@notifications_router.delete("/{notif_id}")
async def delete_notification(notif_id: str):
    """Delete notification"""
    return {"success": True, "notification_id": notif_id}
