"""
Threat Detection Service
Analyzes network traffic and packets for potential threats using anomaly detection
"""

import os
import hashlib
import socket
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime
import ipaddress
import math
import statistics
from urllib.parse import urlsplit
from dotenv import load_dotenv


class ThreatDetectionService:
    def __init__(self):
        self.threats: List[Dict[str, Any]] = []
        self.detected_threats: List[Dict[str, Any]] = []
        self.manual_threats: List[Dict[str, Any]] = []
        self.notifications: List[Dict[str, Any]] = []
        self.blocked_ips: Dict[str, Dict[str, Any]] = {}
        self.blocked_domains: Dict[str, Dict[str, Any]] = {}
        self.threat_state_overrides: Dict[str, Dict[str, Any]] = {}
        self.watched_domain_ip_cache: Dict[str, List[str]] = {}
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
        self.common_service_ports = {
            20, 21, 22, 25, 53, 67, 68, 80, 110, 123, 143, 389, 443,
            465, 587, 636, 993, 995, 1433, 3306, 3389, 5432, 6379, 8080, 8443,
        }

    def _initialize_signatures(self) -> Dict[str, Any]:
        """Initialize known threat signatures and patterns"""
        watched_domain_rules = self._watched_domain_rules_from_env("KNOWN_MALICIOUS_DOMAINS")
        return {
            "known_malicious_ips": self._watchlist_from_env(
                "KNOWN_MALICIOUS_IPS",
                [],
            ),
            "known_malicious_domains": [rule["domain"] for rule in watched_domain_rules],
            "known_malicious_domain_rules": watched_domain_rules,
            "known_malicious_domain_ip_index": self._build_watched_domain_ip_index(watched_domain_rules),
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
        load_dotenv(override=True)
        self.threat_signatures = self._initialize_signatures()
        auto_detected: List[Dict[str, Any]] = []

        if packets:
            # The order matters here: broad traffic checks first, then watched-site
            # matching, then the more behavior-heavy malware patterns.
            auto_detected.extend(await self._detect_statistical_anomalies(packets, traffic_stats))
            auto_detected.extend(await self._detect_port_scanning(packets))
            auto_detected.extend(await self._detect_malicious_site_visits(packets))
            auto_detected.extend(await self._detect_unencrypted_http_activity(packets))
            auto_detected.extend(await self._detect_suspicious_host_activity(packets))
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

    async def hunt_live_threats(
        self,
        packets: List[Dict[str, Any]],
        traffic_stats: Dict[str, Any],
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Rank the strongest live finding from captured traffic.

        Confirmed detections are returned first. If traffic does not cross an alert
        threshold, the hunt falls back to suspicious leads so the UI can still point
        analysts to the most interesting real packet activity without over-claiming.
        """
        if not packets:
            return {
                "packets_analyzed": 0,
                "confirmed_findings": 0,
                "suspicious_leads": 0,
                "best_finding": None,
                "findings": [],
                "timestamp": datetime.now().isoformat(),
            }

        await self.detect_threats(packets, traffic_stats)

        confirmed_findings = [
            {**threat, "classification": "confirmed"}
            for threat in self.detected_threats
        ]
        suspicious_leads = await self._generate_suspicious_leads(packets)

        findings = self._deduplicate_threats(confirmed_findings + suspicious_leads)
        findings = sorted(findings, key=self._finding_rank, reverse=True)
        top_findings = findings[: max(limit, 1)]

        return {
            "packets_analyzed": len(packets),
            "confirmed_findings": len(confirmed_findings),
            "suspicious_leads": len(suspicious_leads),
            "best_finding": top_findings[0] if top_findings else None,
            "findings": top_findings,
            "timestamp": datetime.now().isoformat(),
        }

    async def _generate_suspicious_leads(self, packets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        leads: List[Dict[str, Any]] = []
        leads.extend(await self._hunt_dns_leads(packets))
        leads.extend(await self._hunt_beaconing_leads(packets))
        leads.extend(await self._hunt_outbound_connection_leads(packets))
        leads.extend(await self._hunt_exfiltration_leads(packets))
        return self._deduplicate_threats(leads)

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
                    evidence=[
                        f"Observed {pps} packets in the sampled capture window",
                        f"Threshold configured at {self.pps_threshold} packets per window",
                    ],
                    packet_count=pps,
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
                    evidence=[
                        f"Observed {total_bytes / 1024:.1f} KB across the current capture",
                        f"Threshold configured at {self.bps_threshold / 1024:.1f} KB",
                    ],
                    packet_count=pps,
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
                        evidence=[
                            f"Source touched {unique_ports} destination ports",
                            f"Observed {data['packet_count']} packets from the same source",
                        ],
                        packet_count=data["packet_count"],
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
                        evidence=[
                            f"Observed {data['packet_count']} packets from {src_ip}",
                            f"Traffic concentrated on only {unique_ports} destination ports",
                        ],
                        packet_count=data["packet_count"],
                    )
                )

        return threats

    async def _detect_malicious_site_visits(self, packets: List[Dict]) -> List[Dict]:
        threats = []
        watched_domain_rules = self.threat_signatures.get("known_malicious_domain_rules", [])
        watched_domains = self.threat_signatures.get("known_malicious_domains", [])
        watched_ip_index = self.threat_signatures.get("known_malicious_domain_ip_index", {})
        if not watched_domain_rules:
            return threats

        rule_by_domain = {rule["domain"]: rule for rule in watched_domain_rules}
        # A watched site can be confirmed by a DNS query, an HTTP/TLS host hint,
        # or a destination IP that belongs to the watched domain.
        matched_queries = defaultdict(
            lambda: {
                "packet_count": 0,
                "methods": set(),
                "host_indicators": set(),
                "dns_queries": set(),
                "matched_ips": set(),
                "ports": set(),
            }
        )

        for packet in packets:
            source_ip = packet.get("source_ip")
            destination_ip = packet.get("dest_ip")
            destination_port = packet.get("dest_port")
            query = self._normalize_dns_query(packet.get("dns_query"))
            observed_host = self._normalize_dns_query(packet.get("observed_host"))

            if not source_ip or not self._is_private_ip(source_ip):
                continue

            packet_matches: List[Tuple[str, str, str]] = []
            if observed_host:
                matched_domain = self._match_watched_domain(observed_host, watched_domains)
                if matched_domain:
                    packet_matches.append((matched_domain, "host", observed_host))

            if query:
                matched_domain = self._match_watched_domain(query, watched_domains)
                if matched_domain:
                    packet_matches.append((matched_domain, "dns", query))

            if destination_ip and not self._is_private_ip(destination_ip):
                for matched_domain in watched_ip_index.get(destination_ip, []):
                    packet_matches.append((matched_domain, "ip", destination_ip))

            if not packet_matches:
                continue

            matched_domains_for_packet = set()
            for matched_domain, method, indicator in packet_matches:
                profile = matched_queries[(source_ip, matched_domain)]
                profile["methods"].add(method)
                matched_domains_for_packet.add(matched_domain)

                if method == "host":
                    profile["host_indicators"].add(indicator)
                elif method == "dns":
                    profile["dns_queries"].add(indicator)
                elif method == "ip":
                    profile["matched_ips"].add(indicator)

                if destination_port:
                    profile["ports"].add(destination_port)

            for matched_domain in matched_domains_for_packet:
                matched_queries[(source_ip, matched_domain)]["packet_count"] += 1

        for (source_ip, matched_domain), profile in matched_queries.items():
            rule = rule_by_domain.get(matched_domain, {"severity": "HIGH"})
            methods = sorted(profile["methods"])
            host_indicators = sorted(profile["host_indicators"])
            dns_queries = sorted(profile["dns_queries"])
            matched_ips = sorted(profile["matched_ips"])
            packet_count = profile["packet_count"]
            severity = rule.get("severity", "HIGH")
            threat_score = self._severity_score(severity)

            if methods == ["ip"]:
                severity = self._lower_severity(severity)
                threat_score = max(0.48, threat_score - 0.14)
                match_label = "resolved destination IP"
            elif "host" in methods and "dns" in methods:
                threat_score = min(0.96, threat_score + 0.06)
                match_label = "TLS/HTTP host and DNS lookup"
            elif "host" in methods:
                threat_score = min(0.95, threat_score + 0.04)
                match_label = "TLS/HTTP host"
            elif "dns" in methods and "ip" in methods:
                threat_score = min(0.94, threat_score + 0.03)
                match_label = "DNS lookup and resolved destination IP"
            else:
                match_label = "DNS lookup"

            sample_indicator = host_indicators[0] if host_indicators else dns_queries[0] if dns_queries else matched_domain
            evidence = [
                f"Matched watched site rule {matched_domain} with configured severity {rule.get('severity', 'HIGH')}",
                f"Observed {packet_count} packet(s) from {source_ip} via {match_label.lower()}",
            ]

            if host_indicators:
                evidence.append(f"Captured host indicator: {host_indicators[0]}")
            elif dns_queries:
                evidence.append(f"Captured DNS query: {dns_queries[0]}")

            if matched_ips:
                evidence.append(f"Resolved destination IPs observed: {', '.join(matched_ips[:3])}")
                if methods == ["ip"]:
                    evidence.append("IP-only matches are lower-confidence because shared hosting/CDNs can reuse the same IPs.")

            if profile["ports"]:
                evidence.append(
                    f"Destination ports observed: {', '.join(str(port) for port in sorted(profile['ports']))}"
                )

            threats.append(
                self._build_threat(
                    threat_type="MALICIOUS_SITE_VISIT",
                    source_ip=source_ip,
                    threat_score=threat_score,
                    description=(
                        f"Traffic matched watched site {matched_domain} via {match_label.lower()}"
                    ),
                    severity=severity,
                    destination_host=sample_indicator,
                    destination_ip=matched_ips[0] if matched_ips else None,
                    evidence=evidence,
                    packet_count=packet_count,
                )
            )

        return threats

    async def _detect_unencrypted_http_activity(self, packets: List[Dict]) -> List[Dict]:
        threats = []
        watched_domains = self.threat_signatures.get("known_malicious_domains", [])
        http_profiles = defaultdict(
            lambda: {
                "packet_count": 0,
                "hosts": set(),
                "destination_ips": set(),
                "ports": set(),
            }
        )

        for packet in packets:
            source_ip = packet.get("source_ip")
            destination_ip = packet.get("dest_ip")
            destination_port = packet.get("dest_port")
            observed_host = self._normalize_dns_query(packet.get("observed_host"))
            application_protocol = str(packet.get("application_protocol") or "").upper()

            if not source_ip or not self._is_private_ip(source_ip):
                continue

            is_plain_http = application_protocol in {"HTTP", "HTTP_PROXY_HTTP"} or destination_port in {80, 8080}
            if not is_plain_http:
                continue

            if not observed_host:
                continue

            if self._is_benign_system_host(observed_host):
                continue

            if self._match_watched_domain(observed_host, watched_domains):
                continue

            if destination_ip and self._is_private_ip(destination_ip):
                continue

            identifier = observed_host
            profile = http_profiles[(source_ip, identifier)]
            profile["packet_count"] += 1

            profile["hosts"].add(observed_host)
            if destination_ip:
                profile["destination_ips"].add(destination_ip)
            if isinstance(destination_port, int):
                profile["ports"].add(destination_port)

        for (source_ip, identifier), profile in http_profiles.items():
            packet_count = profile["packet_count"]
            target_host = sorted(profile["hosts"])[0] if profile["hosts"] else None
            target_ip = sorted(profile["destination_ips"])[0] if profile["destination_ips"] else None
            target_label = target_host or target_ip or identifier
            target_port = sorted(profile["ports"])[0] if profile["ports"] else 80

            threats.append(
                self._build_threat(
                    threat_type="UNENCRYPTED_HTTP_ACTIVITY",
                    source_ip=source_ip,
                    threat_score=min(0.66, 0.54 + min(packet_count, 4) * 0.02),
                    description=f"Unencrypted HTTP traffic observed to {target_label}",
                    severity="MEDIUM",
                    destination_host=target_host,
                    destination_ip=target_ip,
                    destination_port=target_port,
                    evidence=[
                        f"Observed {packet_count} plaintext HTTP request event(s) from {source_ip}",
                        f"Observed plaintext HTTP destination port {target_port}",
                        "Plain HTTP exposes browsing traffic without TLS encryption and should be reviewed.",
                    ],
                    packet_count=packet_count,
                )
            )

        return threats

    async def _detect_suspicious_host_activity(self, packets: List[Dict]) -> List[Dict]:
        threats = []
        host_hits = defaultdict(lambda: {"count": 0, "reasons": set()})

        for packet in packets:
            source_ip = packet.get("source_ip")
            indicator = self._normalize_dns_query(packet.get("observed_host"))
            if not indicator or not source_ip or not self._is_private_ip(source_ip):
                continue

            if self._is_benign_system_host(indicator):
                continue

            reasons = self._suspicious_host_reasons(indicator)
            if not reasons:
                continue

            profile = host_hits[(source_ip, indicator)]
            profile["count"] += 1
            profile["reasons"].update(reasons)

        for (source_ip, indicator), profile in host_hits.items():
            reasons = sorted(profile["reasons"])
            strong_signal = self._is_strong_suspicious_host_signal(reasons)
            if len(reasons) < 2 and not strong_signal:
                continue
            if profile["count"] < 2 and not strong_signal:
                continue

            threat_score = min(
                0.82,
                (0.52 if strong_signal else 0.36) + (len(reasons) * 0.06) + min(profile["count"], 5) * 0.015,
            )
            if strong_signal and len(reasons) >= 3:
                severity = "HIGH"
            elif strong_signal or len(reasons) >= 3:
                severity = "MEDIUM"
            else:
                severity = "LOW"
            reason_text = ", ".join(reasons)
            threats.append(
                self._build_threat(
                    threat_type="SUSPICIOUS_HOST_ACTIVITY",
                    source_ip=source_ip,
                    threat_score=threat_score,
                    description=f"Suspicious host indicator observed for {indicator}: {reason_text}",
                    severity=severity,
                    destination_host=indicator,
                    evidence=[
                        f"Observed {profile['count']} host indicator event(s) for {indicator}",
                        f"Matched heuristics: {reason_text}",
                    ],
                    packet_count=profile["count"],
                )
            )

        return threats

    async def _detect_suspicious_ips(self, packets: List[Dict]) -> List[Dict]:
        threats = []
        malicious_ips = set(self.threat_signatures["known_malicious_ips"])
        suspicious_sources = set()
        suspicious_destinations = defaultdict(lambda: {"packet_count": 0, "ports": set()})

        for packet in packets:
            src_ip = packet.get("source_ip")
            dst_ip = packet.get("dest_ip")
            if src_ip and src_ip in malicious_ips:
                suspicious_sources.add(src_ip)
            if (
                src_ip
                and dst_ip
                and dst_ip in malicious_ips
                and self._is_private_ip(src_ip)
            ):
                destination = suspicious_destinations[(src_ip, dst_ip)]
                destination["packet_count"] += 1
                if packet.get("dest_port"):
                    destination["ports"].add(packet["dest_port"])

        for ip in suspicious_sources:
            threats.append(
                self._build_threat(
                    threat_type="MALICIOUS_SOURCE",
                    source_ip=ip,
                    threat_score=0.85,
                    description=f"Traffic from known malicious IP: {ip}",
                    severity="HIGH",
                    evidence=[f"Source IP matched the local malicious IP watchlist: {ip}"],
                )
            )

        for (source_ip, destination_ip), hit in suspicious_destinations.items():
            destination_ports = ", ".join(str(port) for port in sorted(hit["ports"])) or "unknown"
            threats.append(
                self._build_threat(
                    threat_type="MALICIOUS_DESTINATION",
                    source_ip=source_ip,
                    threat_score=min(0.96, 0.78 + min(hit["packet_count"], 10) * 0.015),
                    description=f"Outbound traffic matched watched malicious IP {destination_ip}",
                    severity="HIGH",
                    destination_ip=destination_ip,
                    evidence=[
                        f"Observed {hit['packet_count']} packets from {source_ip} to watched IP {destination_ip}",
                        f"Destination ports observed: {destination_ports}",
                        "Watched IPs come from KNOWN_MALICIOUS_IPS and the local watchlist.",
                    ],
                    packet_count=hit["packet_count"],
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
                        destination_ip=packet.get("dest_ip"),
                        destination_port=dest_port,
                        evidence=[
                            f"Destination port {dest_port} is tagged as high risk",
                            f"Observed protocol {packet.get('protocol', 'Unknown')}",
                        ],
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
                            evidence=[
                                f"ICMP accounts for {percentage:.1f}% of captured packets",
                                f"Observed {count} ICMP packets in the sample",
                            ],
                            packet_count=count,
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
                    destination_ip=target_ip,
                    evidence=[
                        f"{len(src_ips)} unique sources targeted the same destination",
                        f"Single destination observed: {target_ip}",
                    ],
                    packet_count=len(packets),
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
            unique_queries = len(profile["unique_queries"])

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
                        evidence=[
                            f"{suspicious_dns_count} long or high-entropy DNS queries observed",
                            f"Example query: {sample_query}",
                            f"Unique DNS queries from host: {unique_queries}",
                        ],
                        packet_count=unique_queries,
                    )
                )

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
                        evidence=[
                            f"{unique_queries} unique DNS lookups observed from the same host",
                            f"{top_count} queries targeted base domain {top_domain}",
                        ],
                        packet_count=unique_queries,
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
                        destination_ip=dest_ip,
                        destination_port=dest_port,
                        evidence=[
                            f"Average callback interval {average_interval:.1f}s",
                            f"Timing variance {coefficient_of_variation:.2f}",
                            f"{len(ordered_events)} packets with average size {average_size:.0f} B",
                        ],
                        packet_count=len(ordered_events),
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
                        destination_ip=dest_ip,
                        evidence=[
                            f"Outbound volume {bytes_out / 1024:.1f} KB versus {bytes_in / 1024:.1f} KB inbound",
                            f"Outbound to inbound ratio {exfiltration_ratio:.1f}",
                            f"Destination ports observed: {destination_ports}",
                        ],
                        packet_count=packet_count,
                    )
                )

        return threats

    async def _hunt_dns_leads(self, packets: List[Dict]) -> List[Dict]:
        leads = []
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
                len(longest_label) >= 10
                and entropy >= (self.dns_entropy_threshold - 0.2)
                and any(char.isdigit() for char in longest_label)
            ):
                profiles[source_ip]["high_entropy_queries"].append(query)

        for source_ip, profile in profiles.items():
            high_entropy_count = len(profile["high_entropy_queries"])
            long_query_count = len(profile["long_queries"])
            suspicious_dns_count = max(high_entropy_count, long_query_count)
            unique_queries = len(profile["unique_queries"])
            top_domain, top_count = self._top_base_domain(profile["base_domains"])

            if suspicious_dns_count >= 2:
                sample_query = (
                    profile["high_entropy_queries"][0]
                    if profile["high_entropy_queries"]
                    else profile["long_queries"][0]
                )
                score = min(0.64, 0.4 + suspicious_dns_count * 0.08 + unique_queries * 0.01)
                leads.append(
                    self._build_threat(
                        threat_type="SUSPICIOUS_DNS_LEAD",
                        source_ip=source_ip,
                        threat_score=score,
                        description=(
                            f"Live hunt lead: {suspicious_dns_count} unusual DNS queries from "
                            f"{source_ip}, including {sample_query}"
                        ),
                        severity="MEDIUM" if score >= 0.5 else "LOW",
                        status="observed",
                        evidence=[
                            f"{suspicious_dns_count} long or high-entropy DNS queries observed",
                            f"Example query: {sample_query}",
                            f"Unique DNS queries from host: {unique_queries}",
                        ],
                        packet_count=unique_queries,
                        classification="lead",
                    )
                )

            if unique_queries >= 6 and top_count >= 3:
                score = min(0.66, 0.42 + unique_queries * 0.015 + top_count * 0.02)
                leads.append(
                    self._build_threat(
                        threat_type="DNS_TUNNELING_LEAD",
                        source_ip=source_ip,
                        threat_score=score,
                        description=(
                            f"Live hunt lead: repeated unique DNS queries against {top_domain} "
                            f"may indicate DNS tunneling setup"
                        ),
                        severity="MEDIUM" if score >= 0.52 else "LOW",
                        status="observed",
                        evidence=[
                            f"{unique_queries} unique DNS lookups observed from the same host",
                            f"{top_count} queries targeted base domain {top_domain}",
                        ],
                        packet_count=unique_queries,
                        classification="lead",
                    )
                )

        return leads

    async def _hunt_beaconing_leads(self, packets: List[Dict]) -> List[Dict]:
        leads = []
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
            if len(events) < 3:
                continue

            ordered_events = sorted(events, key=lambda event: event["timestamp"])
            intervals = [
                (ordered_events[index]["timestamp"] - ordered_events[index - 1]["timestamp"]).total_seconds()
                for index in range(1, len(ordered_events))
            ]
            if not intervals:
                continue

            average_interval = statistics.mean(intervals)
            if average_interval < 2:
                continue

            interval_stdev = statistics.pstdev(intervals) if len(intervals) > 1 else 0.0
            coefficient_of_variation = interval_stdev / average_interval if average_interval else 1.0

            sizes = [event["size_bytes"] for event in ordered_events]
            average_size = statistics.mean(sizes)
            size_stdev = statistics.pstdev(sizes) if len(sizes) > 1 else 0.0
            size_variation = size_stdev / max(average_size, 1)

            if coefficient_of_variation <= 0.25 and size_variation <= 0.45:
                score = min(
                    0.69,
                    0.44 + len(ordered_events) * 0.025 + (1 - coefficient_of_variation) * 0.08,
                )
                leads.append(
                    self._build_threat(
                        threat_type="BEACONING_LEAD",
                        source_ip=source_ip,
                        threat_score=score,
                        description=(
                            f"Live hunt lead: regular outbound flow to {dest_ip}:{dest_port} "
                            f"every {average_interval:.1f}s across {len(ordered_events)} packets"
                        ),
                        severity="MEDIUM" if score >= 0.55 else "LOW",
                        status="observed",
                        destination_ip=dest_ip,
                        destination_port=dest_port,
                        evidence=[
                            f"Average callback interval {average_interval:.1f}s",
                            f"Timing variance {coefficient_of_variation:.2f}",
                            f"{len(ordered_events)} packets with average size {average_size:.0f} B",
                        ],
                        packet_count=len(ordered_events),
                        classification="lead",
                    )
                )

        return leads

    async def _hunt_outbound_connection_leads(self, packets: List[Dict]) -> List[Dict]:
        leads = []
        flows = defaultdict(lambda: {"packets": 0, "bytes": 0})

        for packet in packets:
            source_ip = packet.get("source_ip")
            dest_ip = packet.get("dest_ip")
            dest_port = packet.get("dest_port")
            if (
                not source_ip
                or not dest_ip
                or not dest_port
                or not self._is_private_ip(source_ip)
                or self._is_private_ip(dest_ip)
            ):
                continue

            if dest_port in self.common_service_ports or dest_port in self.threat_signatures["suspicious_ports"]:
                continue

            flow = flows[(source_ip, dest_ip, dest_port)]
            flow["packets"] += 1
            flow["bytes"] += packet.get("size_bytes", 0)

        for (source_ip, dest_ip, dest_port), flow in flows.items():
            if flow["packets"] < 3:
                continue

            bytes_sent = flow["bytes"]
            score = min(
                0.58,
                0.36 + min(flow["packets"] / 20, 0.1) + min(bytes_sent / 100_000, 0.12),
            )
            leads.append(
                self._build_threat(
                    threat_type="UNCOMMON_OUTBOUND_CONNECTION",
                    source_ip=source_ip,
                    threat_score=score,
                    description=(
                        f"Live hunt lead: repeated outbound connection to {dest_ip}:{dest_port} "
                        f"across {flow['packets']} packets"
                    ),
                    severity="MEDIUM" if score >= 0.5 else "LOW",
                    status="observed",
                    destination_ip=dest_ip,
                    destination_port=dest_port,
                    evidence=[
                        f"{flow['packets']} packets captured for the same outbound flow",
                        f"Transferred {bytes_sent / 1024:.1f} KB to an uncommon external port",
                    ],
                    packet_count=flow["packets"],
                    classification="lead",
                )
            )

        return leads

    async def _hunt_exfiltration_leads(self, packets: List[Dict]) -> List[Dict]:
        leads = []
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
                bytes_out >= 60_000
                and packet_count >= 5
                and exfiltration_ratio >= 2.0
                and average_packet_size >= 600
                and bytes_out < self.exfiltration_bytes_threshold
            ):
                destination_ports = ", ".join(str(port) for port in sorted(flow["ports"])) or "unknown"
                score = min(
                    0.68,
                    0.45
                    + min(bytes_out / 500_000, 0.12)
                    + min(packet_count / 50, 0.06)
                    + min(exfiltration_ratio / 10, 0.05),
                )
                leads.append(
                    self._build_threat(
                        threat_type="EXFILTRATION_LEAD",
                        source_ip=source_ip,
                        threat_score=score,
                        description=(
                            f"Live hunt lead: elevated outbound transfer to {dest_ip} over "
                            f"ports {destination_ports}"
                        ),
                        severity="MEDIUM" if score >= 0.55 else "LOW",
                        status="observed",
                        destination_ip=dest_ip,
                        evidence=[
                            f"Outbound volume {bytes_out / 1024:.1f} KB versus {bytes_in / 1024:.1f} KB inbound",
                            f"Outbound to inbound ratio {exfiltration_ratio:.1f}",
                            f"Destination ports observed: {destination_ports}",
                        ],
                        packet_count=packet_count,
                        classification="lead",
                    )
                )

        return leads

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
                        "destination_ip": threat.get("destination_ip"),
                        "destination_host": threat.get("destination_host"),
                        "destination_port": threat.get("destination_port"),
                        "threat_type": threat.get("type"),
                        "timestamp": threat.get("timestamp"),
                    },
                    "evidence": threat.get("evidence", []),
                    "classification": threat.get("classification", "confirmed"),
                }

        return {"error": "Threat not found"}

    async def respond_to_threat(self, threat_id: str, action: str) -> Dict[str, Any]:
        """Execute a response workflow action for a threat."""
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
            # If the threat points to a domain, we block it at the proxy layer.
            # Otherwise we fall back to the softer dashboard-side IP block.
            blocked_domain = self._domain_to_block_for_threat(threat)
            source_ip = threat.get("source_ip")

            if blocked_domain:
                self.blocked_domains[blocked_domain] = {
                    "blocked_at": now,
                    "reason": threat.get("type"),
                }
                notification_message = f"Website block applied to {blocked_domain}"
                response_message = f"Website block applied to {blocked_domain}"
            elif self._is_blockable_source(source_ip):
                self.blocked_ips[source_ip] = {
                    "blocked_at": now,
                    "reason": threat.get("type"),
                }
                self._ensure_blocked_ip_threat(source_ip, threat)
                notification_message = f"Soft block applied to IP {source_ip}"
                response_message = f"Soft block applied to IP {source_ip}"

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
            "blocked_domain": blocked_domain if action == "BLOCK" and 'blocked_domain' in locals() else None,
        }

    def is_domain_blocked(self, host: Optional[str]) -> bool:
        normalized_host = self._normalize_dns_query(host)
        if not normalized_host:
            return False

        for blocked_domain in self.blocked_domains:
            if normalized_host == blocked_domain or normalized_host.endswith(f".{blocked_domain}"):
                return True

        return False

    def get_blocked_domains(self) -> List[Dict[str, Any]]:
        blocked_entries: List[Dict[str, Any]] = []

        for domain, details in sorted(
            self.blocked_domains.items(),
            key=lambda item: item[1].get("blocked_at", ""),
            reverse=True,
        ):
            blocked_entries.append(
                {
                    "domain": domain,
                    "blocked_at": details.get("blocked_at"),
                    "reason": details.get("reason", "Manual block"),
                }
            )

        return blocked_entries

    def unblock_domain(self, domain: str) -> Dict[str, Any]:
        normalized_domain = self._normalize_dns_query(domain)
        if not normalized_domain:
            return {"success": False, "error": "Domain is required"}

        removed = self.blocked_domains.pop(normalized_domain, None)
        if removed is None:
            return {"success": False, "error": f"{normalized_domain} is not currently blocked"}

        self._release_domain_block_state(normalized_domain)

        now = datetime.now().isoformat()
        self._add_notification(
            title="Website Unblocked",
            message=f"Website unblock applied to {normalized_domain}",
            severity="LOW",
            notification_type="RESPONSE_ACTION",
        )

        return {
            "success": True,
            "message": f"Website unblock applied to {normalized_domain}",
            "domain": normalized_domain,
            "timestamp": now,
        }

    def clear_blocked_domains(self) -> Dict[str, Any]:
        cleared_domains = sorted(self.blocked_domains.keys())
        self.blocked_domains.clear()
        for domain in cleared_domains:
            self._release_domain_block_state(domain)
        now = datetime.now().isoformat()

        self._add_notification(
            title="Blocked Sites Cleared",
            message=(
                "All proxy website blocks were removed"
                if cleared_domains
                else "Blocked sites list was already empty"
            ),
            severity="LOW",
            notification_type="RESPONSE_ACTION",
        )

        return {
            "success": True,
            "message": (
                f"Removed {len(cleared_domains)} blocked site(s)"
                if cleared_domains
                else "Blocked sites list is already empty"
            ),
            "cleared_domains": cleared_domains,
            "timestamp": now,
        }

    def get_notifications(self, threats: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Return recent notifications, including response actions and current threat alerts."""
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
            "MALICIOUS_DESTINATION": ["BLOCK", "BAN_IP", "INVESTIGATE"],
            "MALICIOUS_SITE_VISIT": ["BLOCK_DOMAIN", "INVESTIGATE", "ISOLATE_HOST"],
            "SUSPICIOUS_HOST_ACTIVITY": ["INVESTIGATE", "BLOCK_DOMAIN", "REVIEW_DNS_LOGS"],
            "TRAFFIC_SPIKE": ["INVESTIGATE", "MONITOR"],
            "SYN_FLOOD": ["BLOCK", "ENABLE_SYN_COOKIES"],
            "SUSPICIOUS_PORT_USAGE": ["INVESTIGATE", "ALERT"],
            "SUSPICIOUS_DNS_ACTIVITY": ["INVESTIGATE", "BLOCK_DOMAIN", "ALERT"],
            "DNS_TUNNELING": ["BLOCK_DNS", "INVESTIGATE", "ISOLATE_HOST"],
            "BEACONING_ACTIVITY": ["ISOLATE_HOST", "BLOCK_C2", "INVESTIGATE"],
            "DATA_EXFILTRATION": ["ISOLATE_HOST", "BLOCK_DESTINATION", "ALERT_SOC"],
            "BLOCKED_IP": ["MONITOR", "RELEASE_BLOCK"],
            "SUSPICIOUS_DNS_LEAD": ["INVESTIGATE", "REVIEW_DNS_LOGS"],
            "DNS_TUNNELING_LEAD": ["INVESTIGATE", "REVIEW_DNS_LOGS"],
            "BEACONING_LEAD": ["INVESTIGATE", "REVIEW_PROXY_LOGS"],
            "UNCOMMON_OUTBOUND_CONNECTION": ["INVESTIGATE", "VERIFY_APPLICATION_OWNER"],
            "EXFILTRATION_LEAD": ["INVESTIGATE", "REVIEW_HOST_ACTIVITY"],
        }
        return recommendations.get(threat_type, ["INVESTIGATE"])

    def _domain_to_block_for_threat(self, threat: Dict[str, Any]) -> Optional[str]:
        destination_host = self._normalize_dns_query(threat.get("destination_host"))
        if not destination_host:
            return None

        watched_domain = self._match_watched_domain(
            destination_host,
            self.threat_signatures.get("known_malicious_domains", []),
        )
        return watched_domain or destination_host

    def _build_threat(
        self,
        threat_type: str,
        source_ip: str,
        threat_score: float,
        description: str,
        severity: Optional[str] = None,
        status: str = "active",
        destination_ip: Optional[str] = None,
        destination_host: Optional[str] = None,
        destination_port: Optional[int] = None,
        packet_count: Optional[int] = None,
        evidence: Optional[List[str]] = None,
        classification: str = "confirmed",
    ) -> Dict[str, Any]:
        # Independent helper: every detector funnels through this so the threat
        # shape stays consistent no matter which rule created it.
        threat = {
            "id": self._build_threat_id(
                threat_type=threat_type,
                source_ip=source_ip,
                description=description,
                destination_ip=destination_ip,
                destination_host=destination_host,
                destination_port=destination_port,
            ),
            "type": threat_type,
            "severity": severity or self._calculate_severity(threat_score),
            "threat_score": threat_score,
            "source_ip": source_ip,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "classification": classification,
            "evidence": evidence or [],
        }
        if destination_ip:
            threat["destination_ip"] = destination_ip
        if destination_host:
            threat["destination_host"] = destination_host
        if destination_port is not None:
            threat["destination_port"] = destination_port
        if packet_count is not None:
            threat["packet_count"] = packet_count
        return threat

    def _ensure_blocked_ip_threat(self, source_ip: str, original_threat: Dict[str, Any]) -> None:
        """Create or refresh a BLOCKED_IP threat so it stays visible in the dashboard."""
        description = (
            f"Soft block applied to {source_ip} after {original_threat.get('type')} detection. "
            "Traffic from this IP is marked as blocked in the dashboard response workflow."
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

    def _release_domain_block_state(self, domain: str) -> None:
        normalized_domain = self._normalize_dns_query(domain)
        if not normalized_domain:
            return

        matching_keys = set()

        for threat in self.detected_threats:
            threat_domain = self._domain_to_block_for_threat(threat)
            if threat_domain != normalized_domain:
                continue

            matching_keys.add(self._threat_key(threat))
            if threat.get("status") == "blocked":
                threat["status"] = "active"
            threat.pop("action_taken", None)
            threat.pop("response_time", None)

        for key in matching_keys:
            self.threat_state_overrides.pop(key, None)

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
                str(threat.get("destination_ip", "")),
                str(threat.get("destination_host", "")),
                str(threat.get("destination_port", "")),
                str(threat.get("description", "")),
            ]
        )

    @staticmethod
    def _build_threat_id(
        threat_type: str,
        source_ip: str,
        description: str,
        destination_ip: Optional[str] = None,
        destination_host: Optional[str] = None,
        destination_port: Optional[int] = None,
    ) -> str:
        raw_key = "|".join(
            [
                threat_type,
                source_ip,
                destination_ip or "",
                destination_host or "",
                str(destination_port or ""),
                description,
            ]
        )
        digest = hashlib.sha1(raw_key.encode("utf-8")).hexdigest()[:16]
        return f"threat_{digest}"

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
        if threat_score >= 0.88:
            return "CRITICAL"
        if threat_score >= 0.72:
            return "HIGH"
        if threat_score >= 0.52:
            return "MEDIUM"
        return "LOW"

    def _finding_rank(self, finding: Dict[str, Any]) -> Tuple[float, int, datetime]:
        classification_bonus = 0.2 if finding.get("classification") == "confirmed" else 0.0
        severity_rank = {
            "CRITICAL": 4,
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1,
        }.get(finding.get("severity", "LOW"), 0)
        timestamp = self._parse_packet_timestamp(finding.get("timestamp")) or datetime.min
        return (finding.get("threat_score", 0) + classification_bonus, severity_rank, timestamp)

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

    def _suspicious_host_reasons(self, host: str) -> List[str]:
        reasons: List[str] = []
        labels = [label for label in host.split(".") if label]
        if not labels:
            return reasons

        if any(label.startswith("xn--") for label in labels):
            reasons.append("punycode hostname")

        tld = labels[-1]
        if tld in {"zip", "top", "click", "rest", "gq", "tk", "cf", "ml", "work", "support"}:
            reasons.append(f"high-risk TLD .{tld}")

        if self._looks_like_ip_host(host):
            reasons.append("direct IP host access")

        longest_label = max(labels, key=len)
        if len(longest_label) >= 18 and self._string_entropy(longest_label) >= 3.6:
            reasons.append("high-entropy hostname")

        if len(labels) >= 5:
            reasons.append("deep subdomain chain")

        suspicious_keywords = {"crack", "keygen", "payload", "dropper", "stealer", "exploit", "loader"}
        if any(keyword in host for keyword in suspicious_keywords):
            reasons.append("suspicious host keyword")

        return reasons

    @staticmethod
    def _is_strong_suspicious_host_signal(reasons: List[str]) -> bool:
        reason_set = set(reasons)
        if "direct IP host access" in reason_set:
            return True
        if "punycode hostname" in reason_set and any(reason.startswith("high-risk TLD") for reason in reason_set):
            return True
        if "suspicious host keyword" in reason_set and (
            any(reason.startswith("high-risk TLD") for reason in reason_set)
            or "high-entropy hostname" in reason_set
        ):
            return True
        return False

    @staticmethod
    def _is_benign_system_host(host: str) -> bool:
        normalized_host = host.strip().lower().rstrip(".")
        if not normalized_host:
            return False

        benign_hosts = {
            "captive.apple.com",
            "connectivitycheck.android.com",
            "connectivitycheck.gstatic.com",
            "clients3.google.com",
            "www.msftconnecttest.com",
            "msftconnecttest.com",
            "detectportal.firefox.com",
            "connect.rom.miui.com",
            "nmcheck.gnome.org",
            "networkcheck.kde.org",
            "connectivitycheck.platform.hicloud.com",
            "cp.cloudflare.com",
        }
        benign_suffixes = {
            ".apple.com",
            ".icloud.com",
            ".mzstatic.com",
            ".gstatic.com",
            ".google.com",
            ".googleapis.com",
            ".gvt1.com",
            ".microsoft.com",
            ".msftconnecttest.com",
            ".msftncsi.com",
            ".office.com",
            ".windows.com",
            ".live.com",
            ".mozilla.com",
            ".firefox.com",
            ".miui.com",
            ".xiaomi.com",
            ".hicloud.com",
            ".samsung.com",
            ".samsungcloud.com",
        }

        if normalized_host in benign_hosts:
            return True

        return any(normalized_host.endswith(suffix) for suffix in benign_suffixes)

    @staticmethod
    def _match_watched_domain(query: str, watched_domains: List[str]) -> Optional[str]:
        for watched_domain in watched_domains:
            normalized_domain = watched_domain.strip().lower().rstrip(".")
            if not normalized_domain:
                continue
            if query == normalized_domain or query.endswith(f".{normalized_domain}"):
                return normalized_domain
        return None

    @staticmethod
    def _watchlist_from_env(variable_name: str, defaults: List[str]) -> List[str]:
        values = list(defaults)
        env_value = os.getenv(variable_name, "")
        if env_value:
            values.extend(
                item.strip().lower().rstrip(".")
                for item in env_value.split(",")
                if item.strip()
            )

        return ThreatDetectionService._dedupe_watchlist(values)

    def _watched_domain_rules_from_env(self, variable_name: str) -> List[Dict[str, Any]]:
        rules: List[Dict[str, Any]] = []
        seen_domains = set()
        env_value = os.getenv(variable_name, "")

        for raw_item in env_value.split(","):
            item = raw_item.strip()
            if not item:
                continue

            severity = "HIGH"
            domain = item
            if "=" in item:
                domain, severity_candidate = item.rsplit("=", 1)
                domain = domain.strip()
                severity_candidate = severity_candidate.strip().upper()
                if severity_candidate in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
                    severity = severity_candidate

            normalized_domain = self._normalize_watchlist_domain(domain)
            if not normalized_domain or normalized_domain in seen_domains:
                continue

            seen_domains.add(normalized_domain)
            rules.append(
                {
                    "domain": normalized_domain,
                    "severity": severity,
                    "resolved_ips": self._get_cached_domain_ips(normalized_domain),
                }
            )

        return rules

    @staticmethod
    def _dedupe_watchlist(values: List[str]) -> List[str]:
        deduped: List[str] = []
        seen = set()
        for value in values:
            if not value or value in seen:
                continue
            seen.add(value)
            deduped.append(value)
        return deduped

    @staticmethod
    def _normalize_watchlist_domain(domain: str) -> str:
        candidate = domain.strip()
        if not candidate:
            return ""

        if "://" in candidate or "/" in candidate:
            parsed = urlsplit(candidate if "://" in candidate else f"https://{candidate}")
            candidate = parsed.hostname or candidate

        candidate = candidate.lower().rstrip(".")
        if candidate.startswith("www."):
            candidate = candidate[4:]

        return candidate

    def _build_watched_domain_ip_index(self, watched_domain_rules: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        ip_index: Dict[str, List[str]] = defaultdict(list)
        for rule in watched_domain_rules:
            for ip_value in rule.get("resolved_ips", []):
                if rule["domain"] not in ip_index[ip_value]:
                    ip_index[ip_value].append(rule["domain"])
        return dict(ip_index)

    def _get_cached_domain_ips(self, domain: str) -> List[str]:
        cached = self.watched_domain_ip_cache.get(domain)
        if cached is not None:
            return cached

        resolved = self._resolve_domain_ips(domain)
        self.watched_domain_ip_cache[domain] = resolved
        return resolved

    @staticmethod
    def _resolve_domain_ips(domain: str) -> List[str]:
        resolved: List[str] = []
        try:
            for family, _, _, _, sockaddr in socket.getaddrinfo(domain, 443, type=socket.SOCK_STREAM):
                if family not in {socket.AF_INET, socket.AF_INET6}:
                    continue
                ip_value = sockaddr[0]
                if ip_value not in resolved:
                    resolved.append(ip_value)
        except socket.gaierror:
            return []

        return resolved

    @staticmethod
    def _severity_score(severity: str) -> float:
        return {
            "CRITICAL": 0.92,
            "HIGH": 0.78,
            "MEDIUM": 0.62,
            "LOW": 0.45,
        }.get(severity, 0.62)

    @staticmethod
    def _lower_severity(severity: str) -> str:
        order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        if severity not in order:
            return "MEDIUM"
        index = order.index(severity)
        return order[max(index - 1, 0)]

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
    def _looks_like_ip_host(host: str) -> bool:
        try:
            ipaddress.ip_address(host)
            return True
        except ValueError:
            return False

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
