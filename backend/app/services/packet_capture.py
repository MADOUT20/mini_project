"""
Packet Capture Service
Handles real-time packet capturing and processing
"""

import os
import socket
from scapy.all import sniff, IP, TCP, UDP, ICMP, DNS, DNSQR, Raw, conf, get_if_list
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

    def get_available_interfaces(self) -> Dict[str, Any]:
        """Return capture interfaces that Scapy can see on this host."""
        try:
            interfaces = sorted(set(get_if_list()))
        except Exception:
            interfaces = []

        default_interface = None
        try:
            default_interface = str(conf.iface) if conf.iface else None
        except Exception:
            default_interface = None

        return {
            "interfaces": interfaces,
            "default_interface": default_interface,
        }

    def get_preferred_interface(self) -> Optional[str]:
        """Pick the active interface from the default route when possible."""
        try:
            route = conf.route.route("1.1.1.1")
            if route and route[0]:
                return str(route[0])
        except Exception:
            pass

        try:
            if conf.iface:
                return str(conf.iface)
        except Exception:
            pass

        return None

    def reset_capture_data(self):
        """Clear stored packets and statistics so each capture reflects a fresh sample."""
        self.packets = []
        self.packet_stats = {
            "total_packets": 0,
            "total_bytes": 0,
            "protocols": defaultdict(int),
            "ports": defaultdict(int),
        }
    
    async def capture_packets(self, interface: str = None, count: int = 0, timeout: int = 10):
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
            self.reset_capture_data()

            # Callback function to process each packet
            def packet_callback(packet):
                self._process_packet(packet)
            
            # Start packet capture
            sniff_kwargs = {
                "iface": interface,
                "prn": packet_callback,
                "timeout": timeout,
                "store": True,
            }
            if count and count > 0:
                sniff_kwargs["count"] = count

            packets = sniff(**sniff_kwargs)
            
            return self._format_packets(packets)
        
        except Exception as e:
            message = str(e)
            lower_message = message.lower()

            if "/dev/bpf" in message or "Scapy as root" in message:
                return {
                    "error": (
                        "Packet capture requires admin permissions on macOS. "
                        "Start the app with ./scripts/dev-local-capture.sh or run the backend with sudo. "
                        f"Original error: {message}"
                    )
                }

            if os.name == "nt" and (
                "npcap" in lower_message
                or "winpcap" in lower_message
                or "permission denied" in lower_message
                or "pcap" in lower_message
            ):
                return {
                    "error": (
                        "Packet capture on Windows needs Npcap and an Administrator PowerShell. "
                        "Start the app with .\\scripts\\dev-local-capture.ps1 after installing Npcap. "
                        f"Original error: {message}"
                    )
                }

            return {"error": f"Failed to capture packets: {message}"}
    
    def _process_packet(self, packet):
        """Process and store packet information"""
        packet_info = self._extract_packet_info(packet)
        self._store_packet(packet_info, len(packet))

    def record_proxy_observation(
        self,
        source_ip: Optional[str],
        destination_host: Optional[str],
        destination_port: Optional[int],
        request_bytes: int = 0,
    ) -> Dict[str, Any]:
        """Record a packet-like observation from the local HTTP/HTTPS proxy."""
        packet_info = {
            "timestamp": datetime.now().isoformat(),
            "size_bytes": max(request_bytes, 0),
            "source_ip": source_ip,
            "dest_ip": self._resolve_host_ip(destination_host),
            "protocol": "TCP",
            "application_protocol": "HTTP_PROXY",
            "source_port": None,
            "dest_port": destination_port,
            "flags": [],
            "dns_query": None,
            "dns_query_type": None,
            "observed_host": destination_host.lower() if destination_host else None,
        }
        self._store_packet(packet_info, packet_info["size_bytes"])
        return packet_info

    def _store_packet(self, packet_info: Dict[str, Any], packet_size: int) -> None:
        """Persist a packet-like observation and update aggregate stats."""
        
        # Store packet (maintain max limit)
        if len(self.packets) >= self.max_packets:
            self.packets.pop(0)  # Remove oldest
        
        self.packets.append(packet_info)
        
        # Update statistics
        self.packet_stats["total_packets"] += 1
        self.packet_stats["total_bytes"] += packet_size

        protocol_name = packet_info.get("protocol", "Unknown")
        self.packet_stats["protocols"][protocol_name] += 1

        destination_port = packet_info.get("dest_port")
        if destination_port:
            self.packet_stats["ports"][destination_port] += 1
    
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
            "observed_host": None,
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

        observed_host = self._extract_observed_host(packet)
        if observed_host:
            packet_info["observed_host"] = observed_host
        
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

    def get_proxy_clients(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Summarize client devices observed through the local mobile proxy."""
        clients: Dict[str, Dict[str, Any]] = {}

        for packet in reversed(self.packets):
            if packet.get("application_protocol") != "HTTP_PROXY":
                continue

            source_ip = packet.get("source_ip")
            if not source_ip:
                continue

            profile = clients.setdefault(
                source_ip,
                {
                    "source_ip": source_ip,
                    "request_count": 0,
                    "last_seen": packet.get("timestamp"),
                    "last_host": packet.get("observed_host"),
                    "last_destination_ip": packet.get("dest_ip"),
                    "last_destination_port": packet.get("dest_port"),
                },
            )

            profile["request_count"] += 1

            if packet.get("timestamp") and (
                not profile.get("last_seen")
                or packet["timestamp"] > profile["last_seen"]
            ):
                profile["last_seen"] = packet["timestamp"]
                profile["last_host"] = packet.get("observed_host")
                profile["last_destination_ip"] = packet.get("dest_ip")
                profile["last_destination_port"] = packet.get("dest_port")

        return list(clients.values())[:limit]
    
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

    @staticmethod
    def _extract_observed_host(packet) -> Optional[str]:
        """Extract a hostname indicator from plaintext HTTP or TLS SNI."""
        try:
            if Raw not in packet:
                return None

            payload = bytes(packet[Raw].load)
            if not payload:
                return None

            http_host = PacketCaptureService._extract_http_host(payload)
            if http_host:
                return http_host

            tls_sni = PacketCaptureService._extract_tls_sni(payload)
            if tls_sni:
                return tls_sni
        except Exception:
            return None

        return None

    @staticmethod
    def _resolve_host_ip(host: Optional[str]) -> Optional[str]:
        if not host:
            return None

        try:
            return socket.gethostbyname(host)
        except OSError:
            return None

    @staticmethod
    def _extract_http_host(payload: bytes) -> Optional[str]:
        try:
            if not (
                payload.startswith(b"GET ")
                or payload.startswith(b"POST ")
                or payload.startswith(b"HEAD ")
                or payload.startswith(b"PUT ")
                or payload.startswith(b"OPTIONS ")
            ):
                return None

            text = payload.decode("utf-8", errors="ignore")
            for line in text.split("\r\n"):
                if line.lower().startswith("host:"):
                    return line.split(":", 1)[1].strip().lower()
        except Exception:
            return None

        return None

    @staticmethod
    def _extract_tls_sni(payload: bytes) -> Optional[str]:
        """
        Best-effort TLS ClientHello SNI parser.
        Works for common single-packet ClientHello records.
        """
        try:
            if len(payload) < 5 or payload[0] != 0x16:
                return None

            record_length = int.from_bytes(payload[3:5], "big")
            record_end = min(len(payload), 5 + record_length)
            handshake = payload[5:record_end]
            if len(handshake) < 42 or handshake[0] != 0x01:
                return None

            offset = 4
            offset += 2  # client version
            offset += 32  # random

            if offset >= len(handshake):
                return None

            session_id_len = handshake[offset]
            offset += 1 + session_id_len
            if offset + 2 > len(handshake):
                return None

            cipher_suites_len = int.from_bytes(handshake[offset:offset + 2], "big")
            offset += 2 + cipher_suites_len
            if offset >= len(handshake):
                return None

            compression_methods_len = handshake[offset]
            offset += 1 + compression_methods_len
            if offset + 2 > len(handshake):
                return None

            extensions_len = int.from_bytes(handshake[offset:offset + 2], "big")
            offset += 2
            extensions_end = min(len(handshake), offset + extensions_len)

            while offset + 4 <= extensions_end:
                ext_type = int.from_bytes(handshake[offset:offset + 2], "big")
                ext_len = int.from_bytes(handshake[offset + 2:offset + 4], "big")
                ext_data_start = offset + 4
                ext_data_end = ext_data_start + ext_len
                if ext_data_end > extensions_end:
                    break

                if ext_type == 0x0000 and ext_len >= 5:
                    server_name_list_len = int.from_bytes(handshake[ext_data_start:ext_data_start + 2], "big")
                    name_offset = ext_data_start + 2
                    name_list_end = min(ext_data_end, name_offset + server_name_list_len)

                    while name_offset + 3 <= name_list_end:
                        name_type = handshake[name_offset]
                        name_len = int.from_bytes(handshake[name_offset + 1:name_offset + 3], "big")
                        name_start = name_offset + 3
                        name_end = name_start + name_len
                        if name_end > name_list_end:
                            break
                        if name_type == 0:
                            return handshake[name_start:name_end].decode("utf-8", errors="ignore").lower()
                        name_offset = name_end

                offset = ext_data_end
        except Exception:
            return None

        return None
