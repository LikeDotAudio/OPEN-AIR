#!/usr/bin/env python3
"""Real dnssd tester: browse the network for the configured service type (zeroconf).
    python3 Validations/Protocols/dnssd/dnssd_tester.py [--type _osc._udp] [--timeout S]
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import argparse, time
from _proto_util import config  # noqa: E402
from zeroconf import Zeroconf, ServiceBrowser  # noqa: E402

if __name__ == "__main__":
    cfg, _ = config("dnssd")
    ap = argparse.ArgumentParser(prog="dnssd_tester")
    ap.add_argument("--type", default=cfg.get("service_type", "_osc._udp"))
    ap.add_argument("--domain", default=(cfg.get("domain", "local.") or "local.").rstrip("."))
    ap.add_argument("--timeout", type=float, default=10.0)
    a = ap.parse_args()
    stype = a.type if a.type.endswith(".") else f"{a.type}.{a.domain}."
    found = [0]
    class L:
        def add_service(self, zc, t, name):
            info = zc.get_service_info(t, name, timeout=2000)
            found[0] += 1
            addrs = [".".join(str(b) for b in a4) for a4 in (info.addresses if info else [])]
            print(f"  ⮜ {name}  {addrs}  port={getattr(info,'port',None)}")
        def update_service(self, *a): pass
        def remove_service(self, zc, t, name): print(f"  ✖ removed {name}")
    print(f"👂 [dnssd] browsing '{stype}' for {a.timeout}s…")
    zc = Zeroconf(); ServiceBrowser(zc, stype, L())
    try: time.sleep(a.timeout)
    finally: zc.close()
    print(f"✅ [dnssd] found {found[0]} service(s)."); sys.exit(0 if found[0] else 2)
