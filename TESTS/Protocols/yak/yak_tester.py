# ==========================================
# Header: yak_tester.py
# Purpose: yak_tester.py implementation.
# Description: Logic and implementation for yak_tester.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

#!/usr/bin/env python3
"""Real YAK instrument tester: SCPI *IDN? over TCP.
    python3 Validations/Protocols/yak/yak_tester.py --host 192.168.0.50 [--port 5025] [--cmd '*IDN?']
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import argparse
from _proto_util import config, tcp_probe  # noqa: E402

if __name__ == "__main__":
    cfg, _ = config("yak")
    ap = argparse.ArgumentParser(prog="yak_tester")
    ap.add_argument("--host", default=cfg.get("host", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(cfg.get("port", 5025)))
    ap.add_argument("--cmd", default="*IDN?", help="SCPI command (default *IDN?)")
    ap.add_argument("--timeout", type=float, default=5.0)
    a = ap.parse_args()
    probe = (a.cmd + "\n").encode()
    sys.exit(tcp_probe(a.host, a.port, probe, a.timeout, label="YAK/SCPI"))
