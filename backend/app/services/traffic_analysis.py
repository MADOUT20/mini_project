"""
Traffic Analysis Service
Analyzes network traffic patterns and provides insights
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import statistics

class TrafficAnalysisService:
    def __init__(self):
        self.traffic_data: List[Dict[str, Any]] = []
        self.max_history = 500
    
    async def get_traffic_summary(self, packets: List[Dict[str, Any]], time_range: str = "24h") -> Dict[str, Any]:
        """
        Get traffic summary for specified time range
        """
        if not packets:
            return {
                "total_packets": 0,
                "total_bytes": 0,
                "average_packet_size": 0,
                "packets_per_second": 0,
                "time_range": time_range,
                "summary": "No traffic data available"
            }
        
        total_packets = len(packets)
        total_bytes = sum(p.get("size_bytes", 0) for p in packets)
        avg_size = total_bytes / total_packets if total_packets > 0 else 0
        pps = total_packets  # Simplified for current session
        
        return {
            "total_packets": total_packets,
            "total_bytes": total_bytes,
            "average_packet_size": round(avg_size, 2),
            "packets_per_second": pps,
            "time_range": time_range,
            "timestamp": datetime.now().isoformat()
        }
    
    async def analyze_by_protocol(self, packets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Break down traffic by protocol
        """
        protocol_stats = defaultdict(lambda: {"count": 0, "bytes": 0, "percentage": 0})
        
        if not packets:
            return {"protocols": {}, "total": 0}
        
        total_packets = len(packets)
        total_bytes = sum(p.get("size_bytes", 0) for p in packets)
        
        for packet in packets:
            protocol = packet.get("protocol", "Unknown")
            size = packet.get("size_bytes", 0)
            
            protocol_stats[protocol]["count"] += 1
            protocol_stats[protocol]["bytes"] += size
        
        # Calculate percentages
        for protocol in protocol_stats:
            protocol_stats[protocol]["percentage"] = round(
                (protocol_stats[protocol]["count"] / total_packets * 100), 2
            )
        
        return {
            "protocols": dict(protocol_stats),
            "total_packets": total_packets,
            "total_bytes": total_bytes,
            "timestamp": datetime.now().isoformat()
        }
    
    async def analyze_by_port(self, packets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze traffic by destination ports
        """
        port_stats = defaultdict(lambda: {"count": 0, "protocol": "Unknown"})
        
        if not packets:
            return {"ports": {}, "total": 0}
        
        for packet in packets:
            dest_port = packet.get("dest_port")
            protocol = packet.get("protocol", "Unknown")
            
            if dest_port:
                port_stats[dest_port]["count"] += 1
                port_stats[dest_port]["protocol"] = protocol
        
        # Sort by traffic count and get top 20
        top_ports = dict(
            sorted(port_stats.items(), key=lambda x: x[1]["count"], reverse=True)[:20]
        )
        
        return {
            "top_ports": top_ports,
            "total_unique_ports": len(port_stats),
            "timestamp": datetime.now().isoformat()
        }
    
    async def analyze_by_application(self, packets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Classify traffic by application/port type
        """
        port_to_app = {
            80: "HTTP", 443: "HTTPS", 53: "DNS", 25: "SMTP",
            110: "POP3", 143: "IMAP", 3306: "MySQL", 5432: "PostgreSQL",
            6379: "Redis", 27017: "MongoDB", 22: "SSH", 23: "Telnet",
            21: "FTP", 69: "TFTP", 123: "NTP", 161: "SNMP",
            3389: "RDP", 445: "SMB", 139: "NetBIOS", 8080: "HTTP-Alt"
        }
        
        app_traffic = defaultdict(lambda: {"packets": 0, "bytes": 0, "ports": set()})
        unknown_count = 0
        unknown_bytes = 0
        
        if not packets:
            return {"applications": {}, "total": 0}
        
        for packet in packets:
            dest_port = packet.get("dest_port", 0)
            size = packet.get("size_bytes", 0)
            
            if dest_port in port_to_app:
                app = port_to_app[dest_port]
                app_traffic[app]["packets"] += 1
                app_traffic[app]["bytes"] += size
                app_traffic[app]["ports"].add(dest_port)
            else:
                unknown_count += 1
                unknown_bytes += size
        
        # Convert sets to lists for JSON serialization
        result = {
            "applications": {},
            "unknown": {
                "packets": unknown_count,
                "bytes": unknown_bytes
            },
            "timestamp": datetime.now().isoformat()
        }
        
        for app, stats in app_traffic.items():
            result["applications"][app] = {
                "packets": stats["packets"],
                "bytes": stats["bytes"],
                "ports": sorted(list(stats["ports"]))
            }
        
        return result
    
    async def get_geographic_distribution(self, packets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get traffic distribution by geographic location (simplified IP-based)
        """
        # IP ranges for common regions (simplified)
        ip_regions = {
            "8.8.": "USA (Google)",
            "1.1.": "USA (Cloudflare)",
            "192.168.": "Local Network",
            "10.0.": "Local Network",
            "172.16.": "Local Network",
        }
        
        region_traffic = defaultdict(lambda: {"packets": 0, "bytes": 0})
        
        if not packets:
            return {"regions": {}, "total": 0}
        
        for packet in packets:
            dest_ip = packet.get("dest_ip", "Unknown")
            size = packet.get("size_bytes", 0)
            region = "Other"
            
            for prefix, region_name in ip_regions.items():
                if dest_ip.startswith(prefix):
                    region = region_name
                    break
            
            region_traffic[region]["packets"] += 1
            region_traffic[region]["bytes"] += size
        
        return {
            "regions": dict(region_traffic),
            "timestamp": datetime.now().isoformat(),
            "note": "Geographic distribution based on IP prefix (simplified)"
        }
    
    async def predict_bandwidth_requirements(self, packets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict future bandwidth requirements based on current trends
        """
        if not packets:
            return {
                "prediction": "Insufficient data",
                "current_bandwidth_mbps": 0,
                "projected_bandwidth_mbps": 0
            }
        
        total_bytes = sum(p.get("size_bytes", 0) for p in packets)
        current_bandwidth_mbps = (total_bytes * 8) / 1_000_000  # Convert to Mbps
        
        # Simple linear projection
        avg_packet_size = total_bytes / len(packets) if packets else 0
        growth_factor = 1.15  # Assume 15% growth
        projected_bandwidth = current_bandwidth_mbps * growth_factor
        
        # Capacity recommendations
        if projected_bandwidth < 10:
            recommendation = "Current bandwidth is sufficient"
        elif projected_bandwidth < 100:
            recommendation = "Consider 100 Mbps connection"
        elif projected_bandwidth < 1000:
            recommendation = "Consider 1 Gbps connection"
        else:
            recommendation = "Consider enterprise/multi-Gbps solution"
        
        return {
            "current_bandwidth_mbps": round(current_bandwidth_mbps, 2),
            "projected_bandwidth_mbps": round(projected_bandwidth, 2),
            "growth_assumption": f"{(growth_factor - 1) * 100:.0f}%",
            "recommendation": recommendation,
            "average_packet_size_bytes": round(avg_packet_size, 2),
            "timestamp": datetime.now().isoformat()
        }
    
    async def analyze_connection_patterns(self, packets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze source-destination connection patterns
        """
        if not packets:
            return {
                "unique_sources": 0,
                "unique_destinations": 0,
                "unique_connections": 0,
                "most_active": []
            }
        
        connections = defaultdict(lambda: {"packets": 0, "bytes": 0})
        sources = set()
        destinations = set()
        
        for packet in packets:
            src_ip = packet.get("source_ip")
            dst_ip = packet.get("dest_ip")
            size = packet.get("size_bytes", 0)
            
            if src_ip and dst_ip:
                sources.add(src_ip)
                destinations.add(dst_ip)
                
                connection_key = f"{src_ip} -> {dst_ip}"
                connections[connection_key]["packets"] += 1
                connections[connection_key]["bytes"] += size
        
        # Get top connections
        top_connections = sorted(
            connections.items(),
            key=lambda x: x[1]["packets"],
            reverse=True
        )[:10]
        
        most_active = [
            {
                "connection": conn[0],
                "packets": conn[1]["packets"],
                "bytes": conn[1]["bytes"]
            }
            for conn in top_connections
        ]
        
        return {
            "unique_sources": len(sources),
            "unique_destinations": len(destinations),
            "unique_connections": len(connections),
            "most_active": most_active,
            "timestamp": datetime.now().isoformat()
        }
    
    def store_traffic_sample(self, sample: Dict[str, Any]) -> None:
        """Store traffic sample for historical analysis"""
        self.traffic_data.append({
            "timestamp": datetime.now().isoformat(),
            **sample
        })
        
        # Maintain max history
        if len(self.traffic_data) > self.max_history:
            self.traffic_data.pop(0)
