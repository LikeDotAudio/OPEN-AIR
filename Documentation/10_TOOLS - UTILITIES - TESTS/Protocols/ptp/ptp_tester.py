# ==========================================
# Header: ptp_tester.py
# Purpose: ptp_tester.py implementation.
# Description: Logic and implementation for ptp_tester.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

#!/usr/bin/env python3
"""Real PTP (IEEE 1588) tester: sniff PTP traffic on UDP 319/320 with scapy.
Requires root (packet capture).  sudo python3 Validations/Protocols/ptp/ptp_tester.py [--timeout S]
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import argparse, os
from _proto_util import config  # noqa: E402

if __name__ == "__main__":
    cfg, _ = config("ptp")
    ap = argparse.ArgumentParser(prog="ptp_tester")
    ap.add_argument("--timeout", type=float, default=15.0)
    a = ap.parse_args()
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        print("❌ [PTP] packet sniffing needs root. Re-run with sudo.")
        sys.exit(1)
    from scapy.all import UDP, sniff, bind_layers  # noqa: E402
    try:
        from scapy.contrib.ptp import PTP
        for p in (319, 320):
            bind_layers(UDP, PTP, dport=p); bind_layers(UDP, PTP, sport=p)
    except Exception:
        PTP = None
    n = [0]
    def cb(pkt):
        n[0] += 1
        src = pkt.payload.src if hasattr(pkt.payload, "src") else "?"
        if PTP and pkt.haslayer(PTP):
            p = pkt[PTP]
            print(f"  ⮜ PTP from {src}: type={int(getattr(p,'messageType',-1))} "
                  f"domain={int(getattr(p,'domainNumber',-1))} seq={int(getattr(p,'sequenceId',-1))}")
        else:
            print(f"  ⮜ UDP from {src} on PTP port ({len(bytes(pkt))} bytes)")
    print(f"👂 [PTP] sniffing UDP 319/320 for {a.timeout}s…")
    sniff(filter="udp port 319 or udp port 320", prn=cb, store=0, timeout=a.timeout)
    print(f"✅ [PTP] captured {n[0]} packet(s)."); sys.exit(0 if n[0] else 2)
