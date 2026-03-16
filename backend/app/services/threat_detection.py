"""
Threat Detection Service
Analyzes network traffic and packets for potential threats using anomaly detection
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import statistics

class ThreatDetectionService:
    def __init__(self):
        self.threats: List[Dict[str, Any]] = []
        self.threat_signatures = self._initialize_signatures()
        self.traffic_history: List[Dict[str, Any]] = []
        self.max_history = 100
        
        # Anomaly detection thresholds
        self.pps_threshold = 1000  # packets per second
        self.bps_threshold = 100_000_000  # bytes per second (100 Mbps)
        self.port_scan_threshold = 50  # ports per minute
        self.unique_dst_threshold = 100  # unique destinations
    
    def _initialize_signatures(self) -> Dict[str, Any]:
        """Initialize known threat signatures and patterns"""
        return {
            "known_malicious_ips": [
                "192.168.100.100",  # Example suspicious IPs
                "10.0.0.50",
                "172.16.0.1"
            ],
            "suspicious_ports": [
                4444, 5555, 6666, 7777,  # Common backdoor ports
                31337,  # Back Orifice
                27374,  # SubSeven
                6667,   # IRC botnet
                445,    # SMB exploitation
                139,    # NetBIOS
            ],
            "port_ranges": {
                "well_known": (1, 1023),
                "registered": (1024, 49151),
                "ephemeral": (49152, 65535),
            }
        }
    
    async def detect_threats(self, packets: List[Dict[str, Any]], traffic_stats: Dict[str, Any]):
        """
        Analyze packets for anomalies and threats using multiple detection methods
        
        Args:
            packets: List of captured packets
            traffic_stats: Current traffic statistics
            
        Returns:
            List of detected threats
        """
        detected_threats = []
        
        if not packets:
            return detected_threats
        
        # 1. Statistical Anomaly Detection
        statistical_threats = await self._detect_statistical_anomalies(packets, traffic_stats)
        detected_threats.extend(statistical_threats)
        
        # 2. Port Scanning Detection
        port_scan_threats = await self._detect_port_scanning(packets)
        detected_threats.extend(port_scan_threats)
        
        # 3. Suspicious IP Detection
        suspicious_ip_threats = await self._detect_suspicious_ips(packets)
        detected_threats.extend(suspicious_ip_threats)
        
        # 4. Protocol Anomaly Detection
        protocol_threats = await self._detect_protocol_anomalies(packets)
        detected_threats.extend(protocol_threats)
        
        # 5. DDoS-like Pattern Detection
        ddos_threats = await self._detect_ddos_patterns(packets, traffic_stats)
        detected_threats.extend(ddos_threats)
        
        # Store and deduplicate threats
        self.threats = self._deduplicate_threats(detected_threats)
        
        return self.threats
    
    async def _detect_statistical_anomalies(self, packets: List[Dict], stats: Dict) -> List[Dict]:
        """Detect statistical anomalies in packet patterns"""
        threats = []
        
        pps = len(packets)  # packets per second
        total_bytes = sum(p.get("size_bytes", 0) for p in packets)
        bps = total_bytes
        
        # Check packet rate anomaly
        if pps > self.pps_threshold:
            threat_score = min(0.95, (pps / self.pps_threshold) * 0.7)
            threats.append({
                "id": f"threat_{datetime.now().timestamp()}",
                "type": "TRAFFIC_SPIKE",
                "severity": self._calculate_severity(threat_score),
                "threat_score": threat_score,
                "source_ip": "Network-wide",
                "description": f"Abnormal packet rate: {pps} pps (threshold: {self.pps_threshold})",
                "timestamp": datetime.now().isoformat(),
                "status": "active"
            })
        
        # Check bandwidth anomaly
        if bps > self.bps_threshold:
            threat_score = min(0.95, (bps / self.bps_threshold) * 0.7)
            threats.append({
                "id": f"threat_{datetime.now().timestamp()}_bw",
                "type": "BANDWIDTH_ANOMALY",
                "severity": self._calculate_severity(threat_score),
                "threat_score": threat_score,
                "source_ip": "Network-wide",
                "description": f"Abnormal bandwidth: {bps / 1_000_000:.2f} Mbps (threshold: {self.bps_threshold / 1_000_000:.2f})",
                "timestamp": datetime.now().isoformat(),
                "status": "active"
            })
        
        return threats
    
    async def _detect_port_scanning(self, packets: List[Dict]) -> List[Dict]:
        """Detect port scanning patterns"""
        threats = []
        
        # Group packets by source IP
        sources = defaultdict(lambda: {"ports": set(), "packet_count": 0})
        
        for packet in packets:
            src_ip = packet.get("source_ip")
            dest_port = packet.get("dest_port")
            
            if src_ip and dest_port:
                sources[src_ip]["ports"].add(dest_port)
                sources[src_ip]["packet_count"] += 1
        
        # Detect port scanning: many ports from one source
        for src_ip, data in sources.items():
            unique_ports = len(data["ports"])
            
            if unique_ports > self.port_scan_threshold:
                threat_score = min(0.95, (unique_ports / (self.port_scan_threshold * 2)) * 0.8)
                threats.append({
                    "id": f"threat_{datetime.now().timestamp()}_portscan",
                    "type": "PORT_SCAN",
                    "severity": self._calculate_severity(threat_score),
                    "threat_score": threat_score,
                    "source_ip": src_ip,
                    "description": f"Port scanning detected: {unique_ports} unique ports scanned",
                    "timestamp": datetime.now().isoformat(),
                    "status": "active"
                })
            
            # Detect rapid SYN packets (potential SYN flood)
            if data["packet_count"] > 500 and unique_ports < 5:
                threat_score = 0.75
                threats.append({
                    "id": f"threat_{datetime.now().timestamp()}_synflood",
                    "type": "SYN_FLOOD",
                    "severity": self._calculate_severity(threat_score),
                    "threat_score": threat_score,
                    "source_ip": src_ip,
                    "description": f"Potential SYN flood: {data['packet_count']} packets to {unique_ports} ports",
                    "timestamp": datetime.now().isoformat(),
                    "status": "active"
                })
        
        return threats
    
    async def _detect_suspicious_ips(self, packets: List[Dict]) -> List[Dict]:
        """Detect known suspicious/malicious IPs"""
        threats = []
        malicious_ips = self.threat_signatures["known_malicious_ips"]
        
        suspicious_sources = set()
        suspicious_destinations = set()
        
        for packet in packets:
            src_ip = packet.get("source_ip")
            dst_ip = packet.get("dest_ip")
            
            if src_ip and src_ip in malicious_ips:
                suspicious_sources.add(src_ip)
            
            if dst_ip and dst_ip in malicious_ips:
                suspicious_destinations.add(dst_ip)
        
        # Create threats for detected suspicious IPs
        for ip in suspicious_sources:
            threats.append({
                "id": f"threat_{datetime.now().timestamp()}_malicious",
                "type": "MALICIOUS_SOURCE",
                "severity": "HIGH",
                "threat_score": 0.85,
                "source_ip": ip,
                "description": f"Traffic from known malicious IP: {ip}",
                "timestamp": datetime.now().isoformat(),
                "status": "active"
            })
        
        for ip in suspicious_destinations:
            threats.append({
                "id": f"threat_{datetime.now().timestamp()}_malicious_dst",
                "type": "MALICIOUS_DESTINATION",
                "severity": "MEDIUM",
                "threat_score": 0.7,
                "source_ip": ip,
                "description": f"Connection to known malicious IP: {ip}",
                "timestamp": datetime.now().isoformat(),
                "status": "active"
            })
        
        return threats
    
    async def _detect_protocol_anomalies(self, packets: List[Dict]) -> List[Dict]:
        """Detect unusual protocol behavior"""
        threats = []
        
        protocol_counts = defaultdict(int)
        suspicious_ports = self.threat_signatures["suspicious_ports"]
        
        for packet in packets:
            protocol = packet.get("protocol", "Unknown")
            dest_port = packet.get("dest_port", 0)
            
            protocol_counts[protocol] += 1
            
            # Check for suspicious port usage
            if dest_port in suspicious_ports:
                threats.append({
                    "id": f"threat_{datetime.now().timestamp()}_suspicious_port",
                    "type": "SUSPICIOUS_PORT_USAGE",
                    "severity": "MEDIUM",
                    "threat_score": 0.65,
                    "source_ip": packet.get("source_ip", "Unknown"),
                    "description": f"Connection to suspicious port {dest_port}",
                    "timestamp": datetime.now().isoformat(),
                    "status": "active"
                })
        
        # Check for unusual protocol distribution
        if protocol_counts:
            total = sum(protocol_counts.values())
            for protocol, count in protocol_counts.items():
                percentage = (count / total) * 100
                
                # ICMP should be < 5% normally
                if protocol == "ICMP" and percentage > 20:
                    threats.append({
                        "id": f"threat_{datetime.now().timestamp()}_icmp_anomaly",
                        "type": "ICMP_ANOMALY",
                        "severity": "LOW",
                        "threat_score": 0.5,
                        "source_ip": "Network-wide",
                        "description": f"Unusual ICMP traffic: {percentage:.1f}% of total",
                        "timestamp": datetime.now().isoformat(),
                        "status": "active"
                    })
        
        return threats
    
    async def _detect_ddos_patterns(self, packets: List[Dict], stats: Dict) -> List[Dict]:
        """Detect DDoS-like patterns"""
        threats = []
        
        # Count unique destination IPs
        dst_ips = set(p.get("dest_ip") for p in packets if p.get("dest_ip"))
        src_ips = set(p.get("source_ip") for p in packets if p.get("source_ip"))
        
        # Many sources to same destination = DDoS pattern
        if len(dst_ips) == 1 and len(src_ips) > 20:
            target_ip = list(dst_ips)[0]
            threat_score = min(0.95, (len(src_ips) / 50) * 0.7)
            threats.append({
                "id": f"threat_{datetime.now().timestamp()}_ddos",
                "type": "DDOS_PATTERN",
                "severity": self._calculate_severity(threat_score),
                "threat_score": threat_score,
                "source_ip": f"Multiple sources ({len(src_ips)})",
                "description": f"DDoS pattern detected: {len(src_ips)} sources targeting {target_ip}",
                "timestamp": datetime.now().isoformat(),
                "status": "active"
            })
        
        return threats
    
    def _deduplicate_threats(self, threats: List[Dict]) -> List[Dict]:
        """Remove duplicate threats"""
        seen = set()
        unique_threats = []
        
        for threat in threats:
            threat_key = (threat["type"], threat["source_ip"])
            if threat_key not in seen:
                seen.add(threat_key)
                unique_threats.append(threat)
        
        return unique_threats
    
    def _calculate_severity(self, threat_score: float) -> str:
        """Convert threat score to severity level"""
        if threat_score > 0.8:
            return "CRITICAL"
        elif threat_score > 0.6:
            return "HIGH"
        elif threat_score > 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def analyze_traffic_pattern(self, traffic_data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze traffic patterns and return insights
        """
        if not traffic_data:
            return {"patterns": []}
        
        patterns = {
            "total_samples": len(traffic_data),
            "protocols": defaultdict(int),
            "average_packet_size": 0,
            "peak_rate": 0,
            "anomalies": []
        }
        
        # Calculate statistics
        packet_counts = [d.get("packet_count", 0) for d in traffic_data]
        sizes = [d.get("avg_size", 0) for d in traffic_data]
        
        if sizes:
            patterns["average_packet_size"] = sum(sizes) / len(sizes)
        
        if packet_counts:
            patterns["peak_rate"] = max(packet_counts)
        
        return patterns
    
    async def get_threat_intelligence(self, threat_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed threat intelligence data
        """
        for threat in self.threats:
            if threat["id"] == threat_id:
                return {
                    "threat": threat,
                    "confidence": threat.get("threat_score", 0),
                    "recommended_actions": self._get_recommended_actions(threat["type"]),
                    "ioc": {  # Indicators of Compromise
                        "source_ip": threat.get("source_ip"),
                        "threat_type": threat.get("type"),
                        "timestamp": threat.get("timestamp")
                    }
                }
        
        return {"error": "Threat not found"}
    
    async def respond_to_threat(self, threat_id: str, action: str) -> Dict[str, Any]:
        """
        Execute response action for a threat
        """
        valid_actions = ["BLOCK", "ALERT", "INVESTIGATE", "IGNORE"]
        
        if action not in valid_actions:
            return {
                "success": False,
                "error": f"Invalid action. Must be one of {valid_actions}"
            }
        
        for threat in self.threats:
            if threat["id"] == threat_id:
                threat["status"] = "responded"
                threat["action_taken"] = action
                threat["response_time"] = datetime.now().isoformat()
                
                return {
                    "success": True,
                    "message": f"Threat {threat_id} {action.lower()}ed",
                    "threat_id": threat_id,
                    "action": action
                }
        
        return {"success": False, "error": "Threat not found"}
    
    def _get_recommended_actions(self, threat_type: str) -> List[str]:
        """Get recommended actions for threat type"""
        recommendations = {
            "PORT_SCAN": ["INVESTIGATE", "BLOCK_SOURCE"],
            "DDOS_PATTERN": ["BLOCK", "ALERT_SOC"],
            "MALICIOUS_SOURCE": ["BLOCK", "BAN_IP"],
            "TRAFFIC_SPIKE": ["INVESTIGATE", "MONITOR"],
            "SYN_FLOOD": ["BLOCK", "ENABLE_SYN_COOKIES"],
            "SUSPICIOUS_PORT_USAGE": ["INVESTIGATE", "ALERT"],
        }
        return recommendations.get(threat_type, ["INVESTIGATE"])
