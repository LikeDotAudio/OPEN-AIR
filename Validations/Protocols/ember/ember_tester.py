# ==========================================
# Header: ember_tester.py
# Purpose: ember_tester.py implementation.
# Description: Logic and implementation for ember_tester.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

#!/usr/bin/env python3
"""Real Ember+ (S101/GLOW over TCP) tester: connect + sniff wire bytes.
    python3 Validations/Protocols/ember/ember_tester.py [--host H] [--port N] [--timeout S]
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import argparse
from _proto_util import config, tcp_probe  # noqa: E402

if __name__ == "__main__":
    cfg, _ = config("ember")
    ap = argparse.ArgumentParser(prog="ember_tester")
    ap.add_argument("--host", default=cfg.get("host", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(cfg.get("port", 9000)))
    ap.add_argument("--timeout", type=float, default=5.0)
    a = ap.parse_args()
    sys.exit(tcp_probe(a.host, a.port, None, a.timeout, label="Ember+"))
