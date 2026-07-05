# ==========================================
# Header: rest_tester.py
# Purpose: rest_tester.py implementation.
# Description: Logic and implementation for rest_tester.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

#!/usr/bin/env python3
"""Real REST tester: HTTP request to the configured endpoint.
    python3 Validations/Protocols/rest/rest_tester.py [--path /api] [--method GET] [--host H] [--port N]
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import argparse
from _proto_util import config  # noqa: E402
import requests  # noqa: E402

if __name__ == "__main__":
    cfg, _ = config("rest")
    ap = argparse.ArgumentParser(prog="rest_tester")
    ap.add_argument("--scheme", default=cfg.get("scheme", "http"))
    ap.add_argument("--host", default=cfg.get("host", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(cfg.get("port", 8080)))
    ap.add_argument("--path", default=cfg.get("base_path", "/api"))
    ap.add_argument("--method", default="GET")
    ap.add_argument("--timeout", type=float, default=5.0)
    a = ap.parse_args()
    url = f"{a.scheme}://{a.host}:{a.port}{a.path}"
    print(f"🌐 [REST] {a.method} {url}")
    try:
        r = requests.request(a.method, url, timeout=a.timeout)
    except Exception as e:
        print(f"❌ [REST] request failed: {e}")
        sys.exit(1)
    print(f"  ⮜ {r.status_code} {r.reason}  ({len(r.content)} bytes, {r.headers.get('Content-Type','?')})")
    print(r.text[:1000])
    sys.exit(0 if r.ok else 2)
