from datetime import datetime, timedelta

import pytest

from app.services.threat_detection import ThreatDetectionService


@pytest.mark.asyncio
async def test_hunt_live_threats_prefers_confirmed_detection():
    service = ThreatDetectionService()
    start = datetime(2026, 3, 26, 12, 0, 0)

    packets = [
        {
            "timestamp": (start + timedelta(seconds=index)).isoformat(),
            "source_ip": "192.168.1.10",
            "dest_ip": "8.8.8.8",
            "protocol": "TCP",
            "dest_port": 8443,
            "size_bytes": 15_000,
        }
        for index in range(12)
    ]

    result = await service.hunt_live_threats(packets, {})

    assert result["confirmed_findings"] >= 1
    assert result["best_finding"] is not None
    assert result["best_finding"]["classification"] == "confirmed"
    assert result["best_finding"]["type"] == "DATA_EXFILTRATION"


@pytest.mark.asyncio
async def test_hunt_live_threats_returns_dns_lead_when_alert_threshold_not_met():
    service = ThreatDetectionService()
    start = datetime(2026, 3, 26, 12, 5, 0)

    packets = [
        {
            "timestamp": (start + timedelta(seconds=index)).isoformat(),
            "source_ip": "192.168.1.15",
            "dest_ip": "192.168.1.1",
            "protocol": "UDP",
            "dest_port": 53,
            "size_bytes": 120,
            "dns_query": query,
        }
        for index, query in enumerate(
            [
                "abcdefghijklmnopqrstuvwx123456.example.com",
                "mnopqrstuvwxabcdefghijkl123456.example.com",
            ]
        )
    ]

    result = await service.hunt_live_threats(packets, {})

    assert result["confirmed_findings"] == 0
    assert result["suspicious_leads"] >= 1
    assert result["best_finding"] is not None
    assert result["best_finding"]["classification"] == "lead"
    assert result["best_finding"]["type"] == "SUSPICIOUS_DNS_LEAD"
