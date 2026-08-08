# ==========================================
# Header: sap_tester.py
# Purpose: sap_tester.py implementation.
# Description: Logic and implementation for sap_tester.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

#!/usr/bin/env python3
"""Real SAP/SDP tester: join the SAP multicast group and print announcements.
    python3 Validations/Protocols/sap/sap_tester.py [--group A] [--port N] [--timeout S]
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import argparse, socket, struct, time
from _proto_util import config  # noqa: E402

if __name__ == "__main__":
    cfg, _ = config("sap")
    ap = argparse.ArgumentParser(prog="sap_tester")
    ap.add_argument("--group", default=cfg.get("multicast_address", "239.255.255.255"))
    ap.add_argument("--port", type=int, default=int(cfg.get("port", 9875)))
    ap.add_argument("--timeout", type=float, default=15.0)
    a = ap.parse_args()
    print(f"👂 [SAP] joining {a.group}:{a.port} for {a.timeout}s…")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", a.port))
    mreq = struct.pack("4sl", socket.inet_aton(a.group), socket.INADDR_ANY)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    s.settimeout(1.0)
    end = time.time() + a.timeout
    n = 0
    while time.time() < end:
        try:
            data, addr = s.recvfrom(8192)
        except socket.timeout:
            continue
        n += 1
        # SAP header is >=8 bytes; the SDP payload usually starts at 'v='.
        sdp = data[data.find(b"v="):] if b"v=" in data else data
        print(f"  ⮜ {addr[0]}  ({len(data)} bytes)\n" + sdp.decode("utf-8", "replace")[:600])
    print(f"✅ [SAP] {n} announcement(s).")
    sys.exit(0 if n else 2)
