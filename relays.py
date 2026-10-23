"""VPN Gate relay data model and strict CSV parser."""

from __future__ import annotations

import csv
import io
import socket
from dataclasses import dataclass


@dataclass
class Relay:
    host: str
    ip: str
    ping: int
    speed: int
    sessions: int
    uptime: int
    score: int

    @property
    def speed_text(self) -> str:
        return f"{self.speed / 1_000_000:.0f} Mbps"

    @property
    def ping_text(self) -> str:
        return "—" if self.ping < 0 else f"{self.ping} ms"


def number(value: str, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def parse_relays(payload: str) -> list[Relay]:
    """Parse and rank Japanese relays from the official VPN Gate CSV response."""
    lines = [line for line in payload.splitlines() if not line.startswith("*")]
    parsed: list[Relay] = []
    for item in csv.DictReader(io.StringIO("\n".join(lines))):
        if item.get("CountryShort") != "JP":
            continue
        host, ip = item.get("#HostName", ""), item.get("IP", "")
        try:
            socket.inet_pton(socket.AF_INET, ip)
        except OSError:
            continue
        parsed.append(Relay(
            host=host, ip=ip, ping=number(item.get("Ping", ""), -1),
            speed=number(item.get("Speed", "")), sessions=number(item.get("NumVpnSessions", "")),
            uptime=number(item.get("Uptime", "")), score=number(item.get("Score", "")),
        ))
    parsed.sort(key=lambda relay: (-relay.score, relay.ping if relay.ping >= 0 else 999999))
    return parsed
