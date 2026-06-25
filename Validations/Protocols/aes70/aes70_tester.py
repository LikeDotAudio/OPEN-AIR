#!/usr/bin/env python3
"""Real AES70 (OCA / OCP.1 over TCP) tester: connect + sniff wire bytes.
    python3 Validations/Protocols/aes70/aes70_tester.py [--host H] [--port N] [--timeout S]
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import argparse
from _proto_util import config, tcp_probe  # noqa: E402

if __name__ == "__main__":
    cfg, _ = config("aes70")
    ap = argparse.ArgumentParser(prog="aes70_tester")
    ap.add_argument("--host", default=cfg.get("host", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(cfg.get("port", 50014)))
    ap.add_argument("--timeout", type=float, default=5.0)
    a = ap.parse_args()
    # OCP.1 is binary; we just verify connectivity and dump any OCA notifications.
    sys.exit(tcp_probe(a.host, a.port, None, a.timeout, label="AES70/OCP.1"))
