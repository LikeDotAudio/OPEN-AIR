#!/usr/bin/env python3
"""Real SNMP tester: runs snmpwalk against the agent.
    python3 Validations/Protocols/snmp/snmp_tester.py [--host H] [--oid OID] [--community C] [--version v]
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import argparse, shutil, subprocess
from _proto_util import config  # noqa: E402

if __name__ == "__main__":
    cfg, _ = config("snmp")
    ap = argparse.ArgumentParser(prog="snmp_tester")
    ap.add_argument("--host", default=cfg.get("host", "127.0.0.1"))
    ap.add_argument("--port", default=cfg.get("port", "161"))
    ap.add_argument("--community", default=cfg.get("community", "public"))
    ap.add_argument("--version", default=cfg.get("version", "2c"))
    ap.add_argument("--oid", default="1.3.6.1.2.1.1", help="base OID (default system)")
    a = ap.parse_args()
    if not shutil.which("snmpwalk"):
        print("❌ snmpwalk not found. Install net-snmp (sudo apt install snmp).")
        sys.exit(1)
    target = f"{a.host}:{a.port}" if a.port not in ("161", "") else a.host
    cmd = ["snmpwalk", f"-v{a.version}", "-c", a.community, "-On", target, a.oid]
    print("🔎 [SNMP] " + " ".join(cmd))
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired:
        print("⚠️  [SNMP] snmpwalk timed out. Is snmpd running on the target?")
        sys.exit(2)
    if r.stdout.strip():
        print(r.stdout)
        sys.exit(0)
    print("⚠️  [SNMP] no data." + (("\n" + r.stderr) if r.stderr else ""))
    sys.exit(2)
