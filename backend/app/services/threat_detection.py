"""
Threat Detection Service
Analyzes network traffic and packets for potential threats using anomaly detection
"""

from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime
import ipaddress
import math
import random
import statistics


class ThreatDetectionService:
    def __init__(self):
        self.threats: List[Dict[str, Any]] = []
        self.detected_threats: List[Dict[str, Any]] = []
        self.manual_threats: List[Dict[str, Any]] = []
        self.notifications: List[Dict[str, Any]] = []
        self.blocked_ips: Dict[str, Dict[str, Any]] = {}
        self.threat_state_overrides: Dict[str, Dict[str, Any]] = {}
        self.threat_signatures = self._initialize_signatures()
        self.traffic_history: List[Dict[str, Any]] = []
        self.max_history = 100
        self.max_manual_threats = 100
        self.max_notifications = 100

        # Core anomaly thresholds
        self.pps_threshold = 1000
        self.bps_threshold = 100_000_000
        self.port_scan_threshold = 50
        self.unique_dst_threshold = 100

        # Malware-oriented network behavior thresholds
        self.dns_entropy_threshold = 3.6
        self.dns_long_query_threshold = 30
        self.dns_unique_queries_threshold = 12
        self.beacon_min_events = 5
        self.beacon_min_interval_seconds = 3
        self.beacon_interval_variance = 0.35
        self.exfiltration_bytes_threshold = 150_000
        self.exfiltration_packet_threshold = 12
        self.exfiltration_ratio_threshold = 3.0

    def _initialize_signatures(self) -> Dict[str, Any]:
        """Initialize known threat signatures and patterns"""
        return {
            "known_malicious_ips": [
                "192.168.100.100",
                "10.0.0.50",
                "172.16.0.1",
            ],
            "suspicious_ports": [
                4444, 5555, 6666, 7777,
                31337,
                27374,
                6667,
                445,
                139,
            ],
            "port_ranges": {
                "well_known": (1, 1023),
                "registered": (1024, 49151),
                "ephemeral": (49152, 65535),
            },
        }

    async def detect_threats(self, packets: List[Dict[str, Any]], traffic_stats: Dict[str, Any]):
        """Analyze packets for anomalies and threats using multiple detection methods."""
        auto_detected: List[Dict[str, Any]] = []

        if packets:
            auto_detected.extend(await self._detect_statistical_anomalies(packets, traffic_stats))
            auto_detected.extend(await self._detect_port_scanning(packets))
            auto_detected.extend(await self._detect_suspicious_ips(packets))
            auto_detected.extend(await self._detect_protocol_anomalies(packets))
            auto_detected.extend(await self._detect_ddos_patterns(packets, traffic_stats))
            auto_detected.extend(await self._detect_suspicious_dns_activity(packets))
            auto_detected.extend(await self._detect_beaconing_activity(packets))
            auto_detected.extend(await self._detect_data_exfiltration(packets))

        auto_detected = self._deduplicate_threats(auto_detected)
        self.detected_threats = [self._apply_threat_state(threat) for threat in auto_detected]
        self.threats = self._merge_all_threats()
        return self.threats

    async def _detect_statistical_anomalies(self, packets: List[Dict], stats: Dict) -> List[Dict]:
        threats = []
        pps = len(packets)
        total_bytes = sum(p.get("size_bytes", 0) for p in packets)

        if pps > self.pps_threshold:
            threat_score = min(0.95, (pps / self.pps_threshold) * 0.7)
            threats.append(
                self._build_threat(
                    threat_type="TRAFFIC_SPIKE",
                    source_ip="Network-wide",
                    threat_score=threat_score,
                    description=f"Abnormal packet rate: {pps} pps (threshold: {self.pps_threshold})",
                )
            )

        if total_bytes > self.bps_threshold:
            threat_score = min(0.95, (total_bytes / self.bps_threshold) * 0.7)
            threats.append(
                self._build_threat(
                    threat_type="BANDWIDTH_ANOMALY",
                    source_ip="Network-wide",
                    threat_score=threat_score,
                    description=(
                        f"Abnormal bandwidth: {total_bytes / 1_000_000:.2f} Mbps "
                        f"(threshold: {self.bps_threshold / 1_000_000:.2f})"
                    ),
                )
            )

        return threats

    async def _detect_port_scanning(self, packets: List[Dict]) -> List[Dict]:
        threats = []
        sources = defaultdict(lambda: {"ports": set(), "packet_count": 0})

        for packet in packets:
            src_ip = packet.get("source_ip")
            dest_port = packet.get("dest_port")
            if src_ip and dest_port:
                sources[src_ip]["ports"].add(dest_port)
                sources[src_ip]["packet_count"] += 1

        for src_ip, data in sources.items():
            unique_ports = len(data["ports"])
            if unique_ports > self.port_scan_threshold:
                threat_score = min(0.95, (unique_ports / (self.port_scan_threshold * 2)) * 0.8)
                threats.append(
                    self._build_threat(
                        threat_type="PORT_SCAN",
                        source_ip=src_ip,
                        threat_score=threat_score,
                        description=f"Port scanning detected: {unique_ports} unique ports scanned",
                    )
                )

            if data["packet_count"] > 500 and unique_ports < 5:
                threats.append(
                    self._build_threat(
                        threat_type="SYN_FLOOD",
                        source_ip=src_ip,
                        threat_score=0.75,
                        description=(
                            f"Potential SYN flood: {data['packet_count']} packets "
                            f"to {unique_ports} ports"
                        ),
                    )
                )

        return threats

    async def _detect_suspicious_ips(self, packets: List[Dict]) -> List[Dict]:
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

        for ip in suspicious_sources:
            threats.append(
                self._build_threat(
                    threat_type="MALICIOUS_SOURCE",
                    source_ip=ip,
                    threat_score=0.85,
                    description=f"Traffic from known malicious IP: {ip}",
                    severity="HIGH",
                )
            )

        for ip in suspicious_destinations:
            threats.append(
                self._build_threat(
                    threat_type="MALICIOUS_DESTINATION",
                    source_ip=ip,
                    threat_score=0.7,
                    description=f"Connection to known malicious IP: {ip}",
                    severity="MEDIUM",
                )
            )

        return threats

    async def _detect_protocol_anomalies(self, packets: List[Dict]) -> List[Dict]:
        threats = []
        protocol_counts = defaultdict(int)
        suspicious_ports = self.threat_signatures["suspicious_ports"]

        for packet in packets:
            protocol = packet.get("protocol", "Unknown")
            dest_port = packet.get("dest_port", 0)
            protocol_counts[protocol] += 1

            if dest_port in suspicious_ports:
                threats.append(
                    self._build_threat(
                        threat_type="SUSPICIOUS_PORT_USAGE",
                        source_ip=packet.get("source_ip", "Unknown"),
                        threat_score=0.65,
                        description=f"Connection to suspicious port {dest_port}",
                        severity="MEDIUM",
                    )
                )

        if protocol_counts:
            total = sum(protocol_counts.values())
            for protocol, count in protocol_counts.items():
                percentage = (count / total) * 100
                if protocol == "ICMP" and percentage > 20:
                    threats.append(
                        self._build_threat(
                            threat_type="ICMP_ANOMALY",
                            source_ip="Network-wide",
                            threat_score=0.5,
                            description=f"Unusual ICMP traffic: {percentage:.1f}% of total",
                            severity="LOW",
                        )
                    )

        return threats

    async def _detect_ddos_patterns(self, packets: List[Dict], stats: Dict) -> List[Dict]:
        threats = []
        dst_ips = set(p.get("dest_ip") for p in packets if p.get("dest_ip"))
        src_ips = set(p.get("source_ip") for p in packets if p.get("source_ip"))

        if len(dst_ips) == 1 and len(src_ips) > 20:
            target_ip = list(dst_ips)[0]
            threat_score = min(0.95, (len(src_ips) / 50) * 0.7)
            threats.append(
                self._build_threat(
                    threat_type="DDOS_PATTERN",
                    source_ip=f"Multiple sources ({len(src_ips)})",
                    threat_score=threat_score,
                    description=f"DDoS pattern detected: {len(src_ips)} sources targeting {target_ip}",
                )
            )

        return threats

    async def _detect_suspicious_dns_activity(self, packets: List[Dict]) -> List[Dict]:
        threats = []
        profiles = defaultdict(
            lambda: {
                "unique_queries": set(),
                "high_entropy_queries": [],
                "long_queries": [],
                "base_domains": defaultdict(int),
            }
        )

        for packet in packets:
            query = self._normalize_dns_query(packet.get("dns_query"))
            source_ip = packet.get("source_ip")
            if not query or not source_ip or not self._is_private_ip(source_ip):
                continue

            longest_label = max(query.split("."), key=len, default=query)
            entropy = self._string_entropy(longest_label)
            base_domain = self._base_domain(query)

            profiles[source_ip]["unique_queries"].add(query)
            profiles[source_ip]["base_domains"][base_domain] += 1

            if len(query) >= self.dns_long_query_threshold:
                profiles[source_ip]["long_queries"].append(query)

            if (
                len(longest_label) >= 12
                and entropy >= self.dns_entropy_threshold
                and any(char.isdigit() for char in longest_label)
            ):
                profiles[source_ip]["high_entropy_queries"].append(query)

        for source_ip, profile in profiles.items():
            high_entropy_count = len(profile["high_entropy_queries"])
            long_query_count = len(profile["long_queries"])
            suspicious_dns_count = max(high_entropy_count, long_query_count)

            if suspicious_dns_count >= 3:
                sample_query = (
                    profile["high_entropy_queries"][0]
                    if profile["high_entropy_queries"]
                    else profile["long_queries"][0]
                )
                threat_score = min(0.92, 0.58 + suspicious_dns_count * 0.05)
                threats.append(
                    self._build_threat(
                        threat_type="SUSPICIOUS_DNS_ACTIVITY",
                        source_ip=source_ip,
                        threat_score=threat_score,
                        description=(
                            f"Suspicious DNS behavior: {suspicious_dns_count} unusual queries "
                            f"including {sample_query}"
                        ),
                    )
                )

            unique_queries = len(profile["unique_queries"])
            top_domain, top_count = self._top_base_domain(profile["base_domains"])
            if unique_queries >= self.dns_unique_queries_threshold and top_count >= 5:
                threat_score = min(0.9, 0.55 + (unique_queries / 20) * 0.25)
                threats.append(
                    self._build_threat(
                        threat_type="DNS_TUNNELING",
                        source_ip=source_ip,
                        threat_score=threat_score,
                        description=(
                            f"Possible DNS tunneling: {unique_queries} unique queries with "
                            f"repeated lookups against {top_domain}"
                        ),
                    )
                )

        return threats

    async def _detect_beaconing_activity(self, packets: List[Dict]) -> List[Dict]:
        threats = []
        connections = defaultdict(list)

        for packet in packets:
            source_ip = packet.get("source_ip")
            dest_ip = packet.get("dest_ip")
            dest_port = packet.get("dest_port") or 0
            timestamp = self._parse_packet_timestamp(packet.get("timestamp"))

            if (
                not source_ip
                or not dest_ip
                or timestamp is None
                or not self._is_private_ip(source_ip)
                or self._is_private_ip(dest_ip)
                or packet.get("protocol") not in {"TCP", "UDP"}
            ):
                continue

            connections[(source_ip, dest_ip, dest_port)].append(
                {"timestamp": timestamp, "size_bytes": packet.get("size_bytes", 0)}
            )

        for (source_ip, dest_ip, dest_port), events in connections.items():
            if len(events) < self.beacon_min_events:
                continue

            ordered_events = sorted(events, key=lambda event: event["timestamp"])
            intervals = [
                (ordered_events[index]["timestamp"] - ordered_events[index - 1]["timestamp"]).total_seconds()
                for index in range(1, len(ordered_events))
            ]
            if not intervals:
                continue

            average_interval = statistics.mean(intervals)
            if average_interval < self.beacon_min_interval_seconds:
                continue

            interval_stdev = statistics.pstdev(intervals) if len(intervals) > 1 else 0.0
            coefficient_of_variation = interval_stdev / average_interval if average_interval else 1.0

            sizes = [event["size_bytes"] for event in ordered_events]
            average_size = statistics.mean(sizes)
            size_stdev = statistics.pstdev(sizes) if len(sizes) > 1 else 0.0
            size_variation = size_stdev / max(average_size, 1)

            if coefficient_of_variation <= self.beacon_interval_variance and size_variation <= 0.6:
                threat_score = min(
                    0.93,
                    0.62 + (len(ordered_events) / 20) * 0.15 + (1 - coefficient_of_variation) * 0.12,
                )
                threats.append(
                    self._build_threat(
                        threat_type="BEACONING_ACTIVITY",
                        source_ip=source_ip,
                        threat_score=threat_score,
                        description=(
                            f"Regular outbound communication to {dest_ip}:{dest_port} every "
                            f"{average_interval:.1f}s across {len(ordered_events)} events"
                        ),
                    )
                )

        return threats

    async def _detect_data_exfiltration(self, packets: List[Dict]) -> List[Dict]:
        threats = []
        outbound_flows = defaultdict(lambda: {"bytes_out": 0, "packet_count": 0, "ports": set()})
        inbound_bytes = defaultdict(int)

        for packet in packets:
            source_ip = packet.get("source_ip")
            dest_ip = packet.get("dest_ip")
            size_bytes = packet.get("size_bytes", 0)
            dest_port = packet.get("dest_port")

            if not source_ip or not dest_ip:
                continue

            if self._is_private_ip(source_ip) and not self._is_private_ip(dest_ip):
                flow = outbound_flows[(source_ip, dest_ip)]
                flow["bytes_out"] += size_bytes
                flow["packet_count"] += 1
                if dest_port:
                    flow["ports"].add(dest_port)
            elif not self._is_private_ip(source_ip) and self._is_private_ip(dest_ip):
                inbound_bytes[(dest_ip, source_ip)] += size_bytes

        for (source_ip, dest_ip), flow in outbound_flows.items():
            bytes_out = flow["bytes_out"]
            packet_count = flow["packet_count"]
            bytes_in = inbound_bytes.get((source_ip, dest_ip), 0)
            exfiltration_ratio = bytes_out / max(bytes_in, 1)
            average_packet_size = bytes_out / max(packet_count, 1)

            if (
                bytes_out >= self.exfiltration_bytes_threshold
                and packet_count >= self.exfiltration_packet_threshold
                and exfiltration_ratio >= self.exfiltration_ratio_threshold
                and average_packet_size >= 700
            ):
                threat_score = min(
                    0.94,
                    0.6
                    + min(bytes_out / 1_000_000, 0.2)
                    + min(packet_count / 100, 0.1)
                    + min(exfiltration_ratio / 10, 0.08),
                )
                destination_ports = ", ".join(str(port) for port in sorted(flow["ports"])) or "unknown"
                threats.append(
                    self._build_threat(
                        threat_type="DATA_EXFILTRATION",
                        source_ip=source_ip,
                        threat_score=threat_score,
                        description=(
                            f"Possible exfiltration to {dest_ip} over ports {destination_ports}: "
                            f"{bytes_out / 1024:.1f} KB outbound across {packet_count} packets"
                        ),
                    )
                )

        return threats

    async def get_threat_intelligence(self, threat_id: str) -> Dict[str, Any]:
        """Retrieve detailed threat intelligence data."""
        for threat in self._merge_all_threats():
            if threat["id"] == threat_id:
                return {
                    "threat": threat,
                    "confidence": threat.get("threat_score", 0),
                    "recommended_actions": self._get_recommended_actions(threat["type"]),
                    "ioc": {
                        "source_ip": threat.get("source_ip"),
                        "threat_type": threat.get("type"),
                        "timestamp": threat.get("timestamp"),
                    },
                }

        return {"error": "Threat not found"}

    async def respond_to_threat(self, threat_id: str, action: str) -> Dict[str, Any]:
        """Execute a demo response action for a threat."""
        valid_actions = ["BLOCK", "ALERT", "INVESTIGATE", "IGNORE"]
        if action not in valid_actions:
            return {"success": False, "error": f"Invalid action. Must be one of {valid_actions}"}

        threat = self._find_threat_by_id(threat_id)
        if threat is None:
            return {"success": False, "error": "Threat not found"}

        now = datetime.now().isoformat()
        new_status = {
            "BLOCK": "blocked",
            "ALERT": "alerted",
            "INVESTIGATE": "investigating",
            "IGNORE": "ignored",
        }[action]
        past_tense = {
            "BLOCK": "blocked",
            "ALERT": "alerted",
            "INVESTIGATE": "marked for investigation",
            "IGNORE": "ignored",
        }[action]
        updates = {
            "status": new_status,
            "action_taken": action,
            "response_time": now,
        }

        if self._update_manual_threat(threat_id, updates):
            pass
        else:
            self.threat_state_overrides[self._threat_key(threat)] = updates

        notification_message = f"{action.title()} action applied to {threat.get('source_ip', 'unknown source')}"
        response_message = f"Threat {threat_id} {past_tense}"

        if action == "BLOCK":
            source_ip = threat.get("source_ip")
            if self._is_blockable_source(source_ip):
                self.blocked_ips[source_ip] = {
                    "blocked_at": now,
                    "reason": threat.get("type"),
                }
                self._ensure_blocked_ip_threat(source_ip, threat)
                notification_message = f"Demo block applied to IP {source_ip}"
                response_message = f"Demo block applied to IP {source_ip}"

        self._add_notification(
            title=f"{action.title()} Action Executed",
            message=notification_message,
            severity=threat.get("severity", "MEDIUM"),
            notification_type="RESPONSE_ACTION",
        )

        self.threats = self._merge_all_threats()
        return {
            "success": True,
            "message": response_message,
            "threat_id": threat_id,
            "action": action,
            "status": new_status,
        }

    async def generate_demo_threat(self, scenario: str = "random") -> Dict[str, Any]:
        """Generate one or more demo threats for presentation/testing."""
        scenarios = ["dns", "beaconing", "exfiltration"]
        selected = scenario.lower()
        if selected == "random":
            selected = random.choice(scenarios)

        if selected == "all":
            created_threats = [self._create_demo_threat(item) for item in scenarios]
            self._add_notification(
                title="Demo Threat Pack Generated",
                message="Generated demo DNS, beaconing, and exfiltration threats.",
                severity="HIGH",
                notification_type="DEMO_EVENT",
            )
        elif selected in scenarios:
            created_threats = [self._create_demo_threat(selected)]
            self._add_notification(
                title="Demo Threat Generated",
                message=f"Generated a {selected} demo threat for dashboard testing.",
                severity="MEDIUM",
                notification_type="DEMO_EVENT",
            )
        else:
            return {"success": False, "error": "Invalid demo scenario"}

        self.threats = self._merge_all_threats()
        return {
            "success": True,
            "scenario": selected,
            "threats_created": len(created_threats),
            "threats": created_threats,
        }

    def get_notifications(self, threats: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Return recent notifications, including demo actions and current threat alerts."""
        active_threats = threats if threats is not None else self._merge_all_threats()
        generated_notifications = [
            {
                "id": f"notif_{threat['id']}",
                "type": "THREAT_DETECTED",
                "title": f"Threat Detected: {threat.get('type')}",
                "message": threat.get("description"),
                "severity": threat.get("severity", "MEDIUM"),
                "timestamp": threat.get("timestamp"),
                "read": False,
            }
            for threat in active_threats
            if threat.get("status") not in {"ignored"}
        ]

        combined = self.notifications + generated_notifications
        deduped: List[Dict[str, Any]] = []
        seen_ids = set()

        for notification in sorted(
            combined,
            key=lambda item: self._parse_packet_timestamp(item.get("timestamp")) or datetime.min,
            reverse=True,
        ):
            if notification["id"] in seen_ids:
                continue
            seen_ids.add(notification["id"])
            deduped.append(notification)

        return deduped[:20]

    def _get_recommended_actions(self, threat_type: str) -> List[str]:
        recommendations = {
            "PORT_SCAN": ["INVESTIGATE", "BLOCK_SOURCE"],
            "DDOS_PATTERN": ["BLOCK", "ALERT_SOC"],
            "MALICIOUS_SOURCE": ["BLOCK", "BAN_IP"],
            "TRAFFIC_SPIKE": ["INVESTIGATE", "MONITOR"],
            "SYN_FLOOD": ["BLOCK", "ENABLE_SYN_COOKIES"],
            "SUSPICIOUS_PORT_USAGE": ["INVESTIGATE", "ALERT"],
            "SUSPICIOUS_DNS_ACTIVITY": ["INVESTIGATE", "BLOCK_DOMAIN", "ALERT"],
            "DNS_TUNNELING": ["BLOCK_DNS", "INVESTIGATE", "ISOLATE_HOST"],
            "BEACONING_ACTIVITY": ["ISOLATE_HOST", "BLOCK_C2", "INVESTIGATE"],
            "DATA_EXFILTRATION": ["ISOLATE_HOST", "BLOCK_DESTINATION", "ALERT_SOC"],
            "BLOCKED_IP": ["MONITOR", "RELEASE_BLOCK"],
        }
        return recommendations.get(threat_type, ["INVESTIGATE"])

    def _build_threat(
        self,
        threat_type: str,
        source_ip: str,
        threat_score: float,
        description: str,
        severity: Optional[str] = None,
        status: str = "active",
    ) -> Dict[str, Any]:
        return {
            "id": f"threat_{datetime.now().timestamp()}_{threat_type.lower()}",
            "type": threat_type,
            "severity": severity or self._calculate_severity(threat_score),
            "threat_score": threat_score,
            "source_ip": source_ip,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "status": status,
        }

    def _create_demo_threat(self, scenario: str) -> Dict[str, Any]:
        demo_templates = {
            "dns": {
                "type": "SUSPICIOUS_DNS_ACTIVITY",
                "source_ip": "192.168.1.45",
                "score": 0.78,
                "description": (
                    "[Demo] Workstation generated repeated long DNS queries to "
                    "sync-control-demo.bad.example"
                ),
            },
            "beaconing": {
                "type": "BEACONING_ACTIVITY",
                "source_ip": "192.168.1.52",
                "score": 0.83,
                "description": (
                    "[Demo] Host beaconing every 30 seconds to 45.33.12.9:443 "
                    "with highly regular packet timing"
                ),
            },
            "exfiltration": {
                "type": "DATA_EXFILTRATION",
                "source_ip": "192.168.1.77",
                "score": 0.91,
                "description": (
                    "[Demo] Large outbound transfer to 104.22.11.14:8443 suggests "
                    "data exfiltration behavior"
                ),
            },
        }

        template = demo_templates[scenario]
        threat = self._build_threat(
            threat_type=template["type"],
            source_ip=template["source_ip"],
            threat_score=template["score"],
            description=template["description"],
        )
        threat["demo"] = True
        self.manual_threats.insert(0, threat)
        self.manual_threats = self.manual_threats[:self.max_manual_threats]
        return threat

    def _ensure_blocked_ip_threat(self, source_ip: str, original_threat: Dict[str, Any]) -> None:
        """Create or refresh a demo BLOCKED_IP threat so it stays visible in the dashboard."""
        description = (
            f"Demo block applied to {source_ip} after {original_threat.get('type')} detection. "
            "Traffic from this IP is marked as blocked for presentation purposes."
        )
        existing = next(
            (
                threat
                for threat in self.manual_threats
                if threat.get("type") == "BLOCKED_IP" and threat.get("source_ip") == source_ip
            ),
            None,
        )

        if existing:
            existing.update(
                {
                    "description": description,
                    "severity": "HIGH",
                    "status": "blocked",
                    "timestamp": datetime.now().isoformat(),
                    "action_taken": "BLOCK",
                }
            )
            return

        blocked_threat = self._build_threat(
            threat_type="BLOCKED_IP",
            source_ip=source_ip,
            threat_score=max(original_threat.get("threat_score", 0.7), 0.7),
            description=description,
            severity="HIGH",
            status="blocked",
        )
        blocked_threat["demo"] = True
        blocked_threat["action_taken"] = "BLOCK"
        self.manual_threats.insert(0, blocked_threat)
        self.manual_threats = self.manual_threats[:self.max_manual_threats]

    def _add_notification(
        self,
        title: str,
        message: str,
        severity: str = "MEDIUM",
        notification_type: str = "SYSTEM_EVENT",
    ) -> None:
        self.notifications.insert(
            0,
            {
                "id": f"notification_{datetime.now().timestamp()}",
                "type": notification_type,
                "title": title,
                "message": message,
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
                "read": False,
            },
        )
        self.notifications = self.notifications[:self.max_notifications]

    def _merge_all_threats(self) -> List[Dict[str, Any]]:
        merged = self._deduplicate_threats(self.manual_threats + self.detected_threats)
        return sorted(
            merged,
            key=lambda threat: self._parse_packet_timestamp(threat.get("timestamp")) or datetime.min,
            reverse=True,
        )

    def _find_threat_by_id(self, threat_id: str) -> Optional[Dict[str, Any]]:
        for threat in self._merge_all_threats():
            if threat.get("id") == threat_id:
                return threat
        return None

    def _update_manual_threat(self, threat_id: str, updates: Dict[str, Any]) -> bool:
        for threat in self.manual_threats:
            if threat.get("id") == threat_id:
                threat.update(updates)
                return True
        return False

    def _apply_threat_state(self, threat: Dict[str, Any]) -> Dict[str, Any]:
        updated_threat = dict(threat)
        override = self.threat_state_overrides.get(self._threat_key(updated_threat))
        if override:
            updated_threat.update(override)

        if self._is_blockable_source(updated_threat.get("source_ip")) and updated_threat["source_ip"] in self.blocked_ips:
            updated_threat.setdefault("action_taken", "BLOCK")
            updated_threat["status"] = "blocked"

        return updated_threat

    def _threat_key(self, threat: Dict[str, Any]) -> str:
        return "|".join(
            [
                str(threat.get("type", "")),
                str(threat.get("source_ip", "")),
                str(threat.get("description", "")),
            ]
        )

    def _deduplicate_threats(self, threats: List[Dict]) -> List[Dict]:
        seen = set()
        unique_threats = []
        for threat in threats:
            key = self._threat_key(threat)
            if key in seen:
                continue
            seen.add(key)
            unique_threats.append(threat)
        return unique_threats

    def _calculate_severity(self, threat_score: float) -> str:
        if threat_score > 0.8:
            return "CRITICAL"
        if threat_score > 0.6:
            return "HIGH"
        if threat_score > 0.4:
            return "MEDIUM"
        return "LOW"

    async def analyze_traffic_pattern(self, traffic_data: List[Dict]) -> Dict[str, Any]:
        if not traffic_data:
            return {"patterns": []}

        patterns = {
            "total_samples": len(traffic_data),
            "protocols": defaultdict(int),
            "average_packet_size": 0,
            "peak_rate": 0,
            "anomalies": [],
        }
        packet_counts = [data.get("packet_count", 0) for data in traffic_data]
        sizes = [data.get("avg_size", 0) for data in traffic_data]

        if sizes:
            patterns["average_packet_size"] = sum(sizes) / len(sizes)
        if packet_counts:
            patterns["peak_rate"] = max(packet_counts)

        return patterns

    @staticmethod
    def _parse_packet_timestamp(timestamp: Optional[str]) -> Optional[datetime]:
        if not timestamp:
            return None
        try:
            return datetime.fromisoformat(timestamp)
        except ValueError:
            return None

    @staticmethod
    def _normalize_dns_query(query: Optional[str]) -> Optional[str]:
        if not query:
            return None
        return query.strip().lower().rstrip(".")

    @staticmethod
    def _base_domain(query: str) -> str:
        labels = [label for label in query.split(".") if label]
        if len(labels) >= 2:
            return ".".join(labels[-2:])
        return query

    @staticmethod
    def _top_base_domain(base_domains: Dict[str, int]) -> Tuple[str, int]:
        if not base_domains:
            return "unknown", 0
        return max(base_domains.items(), key=lambda item: item[1])

    @staticmethod
    def _string_entropy(text: str) -> float:
        if not text:
            return 0.0
        counts = defaultdict(int)
        for char in text:
            counts[char] += 1
        length = len(text)
        entropy = 0.0
        for count in counts.values():
            probability = count / length
            entropy -= probability * math.log2(probability) if probability else 0.0
        return entropy

    @staticmethod
    def _is_private_ip(ip_value: str) -> bool:
        try:
            ip_object = ipaddress.ip_address(ip_value)
            return (
                ip_object.is_private
                or ip_object.is_loopback
                or ip_object.is_link_local
                or ip_object.is_reserved
            )
        except ValueError:
            return False

    @staticmethod
    def _is_blockable_source(source_ip: Optional[str]) -> bool:
        if not source_ip:
            return False
        return source_ip not in {"Network-wide", "Unknown"} and not source_ip.startswith("Multiple sources")
