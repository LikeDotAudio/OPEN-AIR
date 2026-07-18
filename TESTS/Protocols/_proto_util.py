# ==========================================
# Header: _proto_util.py
# Purpose: _proto_util.py implementation.
# Description: Logic and implementation for _proto_util.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

#!/usr/bin/env python3
"""Shared helpers for the real-protocol testers under Validations/Protocols/.

Each <proto>/<proto>_tester.py is a standalone wire-level tester for its protocol
(OSC/UDP, MIDI, SNMP, PTP, REST/HTTP, NMOS, DNS-SD, mDNS, SAP, Ember+, VISA,
WebSocket, raw-TCP for AES70/SMPTE2138, SCPI for YAK, MQTT bus monitor). They all
read connection params from BackEnd/ComProtocols/openair-<proto>/config.ini.
"""
import configparser
import pathlib
import socket

ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPROTOCOLS = ROOT / "BackEnd" / "ComProtocols"


# Inline comment: Logic for config
def config(proto):
    """Return ({key: value}, ini_path) for openair-<proto>/config.ini."""
    ini = COMPROTOCOLS / f"openair-{proto}" / "config.ini"
    c = configparser.ConfigParser()
    if ini.is_file():
        c.read(ini, encoding="utf-8")
    sect = proto if c.has_section(proto) else (c.sections()[0] if c.sections() else None)
    return (dict(c.items(sect)) if sect else {}), ini


# Inline comment: Logic for hexdump
def hexdump(data, width=16):
    out = []
    for i in range(0, len(data), width):
        chunk = data[i:i + width]
        hexs = " ".join(f"{b:02x}" for b in chunk)
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        out.append(f"  {i:04x}  {hexs:<{width*3}}  {text}")
    return "\n".join(out)


# Inline comment: Logic for tcp_probe
def tcp_probe(host, port, probe=None, timeout=5.0, label="TCP"):
    """Connect to host:port, optionally send `probe` bytes, read whatever comes
    back within `timeout`, and hexdump it. Returns exit code (0 ok, 2 no data,
    1 connect failure). A real connectivity + wire-traffic test."""
    print(f"🔌 [{label}] connecting to {host}:{port} (timeout {timeout}s)…")
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
    except OSError as e:
        print(f"❌ [{label}] connect failed: {e}")
        return 1
    print(f"✅ [{label}] connected.")
    sock.settimeout(timeout)
    try:
        if probe:
            sock.sendall(probe)
            print(f"  ⮞ sent {len(probe)} bytes: {probe!r}")
        chunks = []
        try:
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                chunks.append(data)
                if sum(len(c) for c in chunks) > 65536:
                    break
        except socket.timeout:
            pass
        blob = b"".join(chunks)
        if blob:
            print(f"  ⮜ received {len(blob)} bytes:\n{hexdump(blob)}")
            return 0
        print(f"⚠️  [{label}] connected but no data within {timeout}s.")
        return 2
    finally:
        sock.close()
