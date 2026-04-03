from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# These schemas are typed data containers. They describe what a packet,
# threat, notification, or settings object should look like.
class Packet(BaseModel):
    id: int
    timestamp: datetime
    source_ip: str
    dest_ip: str
    source_port: int
    dest_port: int
    protocol: str
    size_bytes: int
    flags: str

class Threat(BaseModel):
    id: int
    timestamp: datetime
    type: str
    severity: str
    source_ip: str
    destination_ip: str
    description: str
    confidence_score: float
    status: str

class TrafficData(BaseModel):
    timestamp: datetime
    incoming_mbps: float
    outgoing_mbps: float
    total_connections: int
    active_connections: int

class Notification(BaseModel):
    id: int
    timestamp: datetime
    type: str
    title: str
    message: str
    severity: str
    read: bool

class User(BaseModel):
    id: int
    username: str
    email: str
    role: str
    status: str
    last_login: datetime

class SystemSettings(BaseModel):
    system_name: str
    version: str
    notification_email: str
    log_retention_days: int
    auto_backup_enabled: bool
    backup_interval_hours: int
    max_concurrent_users: int
    threat_threshold: float
