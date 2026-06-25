#!/usr/bin/env python3
"""Real VISA tester: list instruments, or open a resource and query *IDN?.
    python3 Validations/Protocols/visa/visa_tester.py list
    python3 Validations/Protocols/visa/visa_tester.py idn [--resource RSRC]
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import argparse
from _proto_util import config  # noqa: E402
import pyvisa  # noqa: E402

if __name__ == "__main__":
    cfg, _ = config("visa")
    ap = argparse.ArgumentParser(prog="visa_tester")
    ap.add_argument("action", nargs="?", default="list", choices=["list", "idn"])
    ap.add_argument("--resource", default=cfg.get("resource", ""))
    ap.add_argument("--timeout", type=int, default=int(cfg.get("timeout_ms", 5000)))
    a = ap.parse_args()
    try:
        rm = pyvisa.ResourceManager("@py")
    except Exception:
        rm = pyvisa.ResourceManager()
    res = list(rm.list_resources())
    print(f"🔎 [VISA] {len(res)} resource(s): {res or '(none)'}")
    if a.action == "list":
        sys.exit(0 if res else 2)
    target = a.resource or (res[0] if res else None)
    if not target:
        print("❌ [VISA] no resource to query (specify --resource)."); sys.exit(1)
    print(f"🔌 [VISA] opening {target} …")
    try:
        inst = rm.open_resource(target); inst.timeout = a.timeout
        print(f"  ⮜ *IDN? -> {inst.query('*IDN?').strip()}")
        inst.close()
    except Exception as e:
        print(f"❌ [VISA] query failed: {e}"); sys.exit(2)
    sys.exit(0)
