#!/usr/bin/env python3
"""Real NMOS tester: query the IS-04 registry/query API over HTTP.
    python3 Validations/Protocols/nmos/nmos_tester.py [--registry URL] [--path /x-nmos/query/v1.3/]
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import argparse
from _proto_util import config  # noqa: E402
import requests  # noqa: E402

if __name__ == "__main__":
    cfg, _ = config("nmos")
    base = cfg.get("registry_url") or f"http://{cfg.get('host','127.0.0.1')}:{cfg.get('port','8080')}"
    ap = argparse.ArgumentParser(prog="nmos_tester")
    ap.add_argument("--registry", default=base)
    ap.add_argument("--path", default="/x-nmos/query/v1.3/")
    ap.add_argument("--timeout", type=float, default=5.0)
    a = ap.parse_args()
    url = a.registry.rstrip("/") + a.path
    print(f"🌐 [NMOS] GET {url}")
    try:
        r = requests.get(url, timeout=a.timeout)
    except Exception as e:
        print(f"❌ [NMOS] request failed: {e}")
        sys.exit(1)
    print(f"  ⮜ {r.status_code} {r.reason}")
    print(r.text[:1500])
    sys.exit(0 if r.ok else 2)
