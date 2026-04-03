"""
Helper utilities for the application
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict

def log_event(event_type: str, details: Dict[str, Any]):
    """Log an event to the system"""
    # Small standalone helper for structured console logging.
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "details": details
    }
    print(f"[LOG] {json.dumps(log_entry)}")
    return log_entry

def hash_ip(ip: str) -> str:
    """Hash an IP address for privacy"""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]

def parse_packet_data(raw_packet: bytes) -> Dict[str, Any]:
    """Parse raw packet data into structured format"""
    # This is currently a placeholder and is not part of the active backend flow.
    pass

def format_bytes(bytes_value: int) -> str:
    """Format bytes into human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def is_private_ip(ip: str) -> bool:
    """Check if IP is private/internal"""
    private_ranges = [
        ("10.0.0.0", "10.255.255.255"),
        ("172.16.0.0", "172.31.255.255"),
        ("192.168.0.0", "192.168.255.255"),
        ("127.0.0.0", "127.255.255.255"),
    ]
    
    ip_parts = [int(x) for x in ip.split('.')]
    ip_int = (ip_parts[0] << 24) + (ip_parts[1] << 16) + (ip_parts[2] << 8) + ip_parts[3]
    
    for start, end in private_ranges:
        start_parts = [int(x) for x in start.split('.')]
        end_parts = [int(x) for x in end.split('.')]
        start_int = (start_parts[0] << 24) + (start_parts[1] << 16) + (start_parts[2] << 8) + start_parts[3]
        end_int = (end_parts[0] << 24) + (end_parts[1] << 16) + (end_parts[2] << 8) + end_parts[3]
        
        if start_int <= ip_int <= end_int:
            return True
    
    return False
