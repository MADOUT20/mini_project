"""
Packet Capture Service
Handles real-time packet capturing and processing
"""

from scapy.all import sniff, IP, TCP, UDP, ICMP, DNS, DNSQR
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime
from queue import Queue

class PacketCaptureService:
    def __init__(self, max_packets: int = 1000):
        self.packets = []
        self.max_packets = max_packets
        self.packet_queue = Queue()
        self.capture_thread = None
        self.is_capturing = False
        self.packet_stats = {
            "total_packets": 0,
            "total_bytes": 0,
            "protocols": defaultdict(int),
            "ports": defaultdict(int),
        }
    
    async def capture_packets(self, interface: str = None, count: int = 100, timeout: int = 10):
        """
        Capture packets from network interface using Scapy.
        
        Args:
            interface: Network interface name (e.g., 'eth0', 'en0'). If None, uses default.
            count: Number of packets to capture
            timeout: Timeout in seconds
            
        Returns:
            List of captured packets
        """
        try:
            # Callback function to process each packet
            def packet_callback(packet):
                self._process_packet(packet)
            
            # Start packet capture
            packets = sniff(
                iface=interface,
                prn=packet_callback,
                count=count,
                timeout=timeout,
                store=True
            )
            
            return self._format_packets(packets)
        
        except Exception as e:
            return {"error": f"Failed to capture packets: {str(e)}"}
    
    def _process_packet(self, packet):
        """Process and store packet information"""
        packet_info = self._extract_packet_info(packet)
        
        # Store packet (maintain max limit)
        if len(self.packets) >= self.max_packets:
            self.packets.pop(0)  # Remove oldest
        
        self.packets.append(packet_info)
        
        # Update statistics
        self.packet_stats["total_packets"] += 1
        self.packet_stats["total_bytes"] += len(packet)
        
        if IP in packet:
            ip_layer = packet[IP]
            protocol = ip_layer.proto
            proto_name = self._get_protocol_name(protocol)
            self.packet_stats["protocols"][proto_name] += 1
        
        # Track ports
        if TCP in packet:
            dst_port = packet[TCP].dport
            self.packet_stats["ports"][dst_port] += 1
        elif UDP in packet:
            dst_port = packet[UDP].dport
            self.packet_stats["ports"][dst_port] += 1
    
    def _extract_packet_info(self, packet) -> Dict[str, Any]:
        """Extract relevant information from a packet"""
        packet_info = {
            "timestamp": self._packet_timestamp(packet),
            "size_bytes": len(packet),
            "source_ip": None,
            "dest_ip": None,
            "protocol": "Unknown",
            "application_protocol": None,
            "source_port": None,
            "dest_port": None,
            "flags": [],
            "dns_query": None,
            "dns_query_type": None,
        }
        
        # IP layer
        if IP in packet:
            ip_layer = packet[IP]
            packet_info["source_ip"] = ip_layer.src
            packet_info["dest_ip"] = ip_layer.dst
            packet_info["protocol"] = self._get_protocol_name(ip_layer.proto)
        
        # TCP layer
        if TCP in packet:
            tcp_layer = packet[TCP]
            packet_info["source_port"] = tcp_layer.sport
            packet_info["dest_port"] = tcp_layer.dport
            packet_info["flags"] = self._parse_tcp_flags(tcp_layer.flags)
            packet_info["protocol"] = "TCP"
        
        # UDP layer
        elif UDP in packet:
            udp_layer = packet[UDP]
            packet_info["source_port"] = udp_layer.sport
            packet_info["dest_port"] = udp_layer.dport
            packet_info["protocol"] = "UDP"
        
        # ICMP layer
        elif ICMP in packet:
            packet_info["protocol"] = "ICMP"
            packet_info["flags"] = [f"Type: {packet[ICMP].type}"]

        if DNS in packet:
            packet_info["application_protocol"] = "DNS"
            dns_query, dns_query_type = self._extract_dns_query(packet)
            packet_info["dns_query"] = dns_query
            packet_info["dns_query_type"] = dns_query_type
        
        return packet_info
    
    async def filter_packets(self, **filters) -> List[Dict[str, Any]]:
        """
        Filter captured packets by various criteria.
        
        Supported filters:
            - source_ip: Filter by source IP
            - dest_ip: Filter by destination IP
            - protocol: Filter by protocol (TCP, UDP, ICMP)
            - port: Filter by port (source or destination)
            - min_size: Minimum packet size in bytes
            - max_size: Maximum packet size in bytes
        """
        filtered = self.packets
        
        if "source_ip" in filters:
            filtered = [p for p in filtered if p.get("source_ip") == filters["source_ip"]]
        
        if "dest_ip" in filters:
            filtered = [p for p in filtered if p.get("dest_ip") == filters["dest_ip"]]
        
        if "protocol" in filters:
            filtered = [p for p in filtered if p.get("protocol") == filters["protocol"]]
        
        if "port" in filters:
            port = filters["port"]
            filtered = [p for p in filtered if p.get("source_port") == port or p.get("dest_port") == port]
        
        if "min_size" in filters:
            filtered = [p for p in filtered if p.get("size_bytes", 0) >= filters["min_size"]]
        
        if "max_size" in filters:
            filtered = [p for p in filtered if p.get("size_bytes", 0) <= filters["max_size"]]
        
        return filtered
    
    async def get_packet_statistics(self) -> Dict[str, Any]:
        """Get statistics about captured packets"""
        return {
            "total_packets": self.packet_stats["total_packets"],
            "total_bytes": self.packet_stats["total_bytes"],
            "average_packet_size": (
                self.packet_stats["total_bytes"] / self.packet_stats["total_packets"]
                if self.packet_stats["total_packets"] > 0 else 0
            ),
            "protocols": dict(self.packet_stats["protocols"]),
            "top_ports": self._get_top_ports(10),
            "stored_packets": len(self.packets)
        }
    
    def _get_top_ports(self, limit: int = 10) -> Dict[int, int]:
        """Get top N ports by traffic"""
        sorted_ports = sorted(
            self.packet_stats["ports"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        return dict(sorted_ports[:limit])
    
    def _format_packets(self, scapy_packets) -> List[Dict[str, Any]]:
        """Convert Scapy packets to JSON-serializable format"""
        return [self._extract_packet_info(pkt) for pkt in scapy_packets]
    
    @staticmethod
    def _get_protocol_name(protocol_number: int) -> str:
        """Convert protocol number to name"""
        protocol_map = {
            1: "ICMP",
            6: "TCP",
            17: "UDP",
            41: "IPv6",
        }
        return protocol_map.get(protocol_number, f"Other({protocol_number})")
    
    @staticmethod
    def _parse_tcp_flags(flags) -> List[str]:
        """Parse TCP flags into readable format"""
        flag_names = []
        if flags & 0x01:  # FIN
            flag_names.append("FIN")
        if flags & 0x02:  # SYN
            flag_names.append("SYN")
        if flags & 0x04:  # RST
            flag_names.append("RST")
        if flags & 0x08:  # PSH
            flag_names.append("PSH")
        if flags & 0x10:  # ACK
            flag_names.append("ACK")
        if flags & 0x20:  # URG
            flag_names.append("URG")
        return flag_names if flag_names else ["None"]

    @staticmethod
    def _packet_timestamp(packet) -> str:
        """Convert the packet capture time into an ISO timestamp."""
        packet_time = getattr(packet, "time", None)
        if packet_time is None:
            return datetime.now().isoformat()

        try:
            return datetime.fromtimestamp(float(packet_time)).isoformat()
        except Exception:
            return datetime.now().isoformat()

    @staticmethod
    def _extract_dns_query(packet) -> tuple[Optional[str], Optional[str]]:
        """Extract a DNS query name and type when present."""
        try:
            if DNS in packet and packet[DNS].qd and DNSQR in packet:
                query_name = packet[DNSQR].qname.decode(errors="ignore").rstrip(".")
                query_type = str(packet[DNSQR].qtype)
                return query_name, query_type
        except Exception:
            pass

        return None, None
