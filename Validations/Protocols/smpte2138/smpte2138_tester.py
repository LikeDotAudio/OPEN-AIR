#!/usr/bin/env python3
"""Real SMPTE ST 2138 (CCM / protobuf over TCP) tester: connect + sniff bytes.
    python3 Validations/Protocols/smpte2138/smpte2138_tester.py [--host H] [--port N] [--timeout S]
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import argparse
from _proto_util import config, tcp_probe  # noqa: E402

if __name__ == "__main__":
    cfg, _ = config("smpte2138")
    ap = argparse.ArgumentParser(prog="smpte2138_tester")
    ap.add_argument("--host", default=cfg.get("host", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(cfg.get("port", 50051)))
    ap.add_argument("--timeout", type=float, default=5.0)
    a = ap.parse_args()
    sys.exit(tcp_probe(a.host, a.port, None, a.timeout, label="ST2138"))
