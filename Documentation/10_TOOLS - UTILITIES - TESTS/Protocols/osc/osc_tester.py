# ==========================================
# Header: osc_tester.py
# Purpose: osc_tester.py implementation.
# Description: Logic and implementation for osc_tester.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

#!/usr/bin/env python3
"""Real OSC tester (headless UDP). Listen for OSC, or send a test message.
    python3 Validations/Protocols/osc/osc_tester.py listen [--port N] [--timeout S]
    python3 Validations/Protocols/osc/osc_tester.py send --addr /ch/1/fader --args 0.75
(GUI variant: osc_monitor.py)
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import argparse, time
from _proto_util import config  # noqa: E402
from pythonosc.dispatcher import Dispatcher          # noqa: E402
from pythonosc.osc_server import BlockingOSCUDPServer  # noqa: E402
from pythonosc.udp_client import SimpleUDPClient        # noqa: E402
import threading  # noqa: E402

if __name__ == "__main__":
    cfg, _ = config("osc")
    ap = argparse.ArgumentParser(prog="osc_tester")
    ap.add_argument("action", nargs="?", default="listen", choices=["listen", "send"])
    ap.add_argument("--host", default=cfg.get("host", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(cfg.get("port", 8000)))
    ap.add_argument("--addr", default="/test/openair")
    ap.add_argument("--args", nargs="*", default=["1.0"])
    ap.add_argument("--timeout", type=float, default=15.0)
    a = ap.parse_args()
    if a.action == "send":
        host = "127.0.0.1" if a.host == "0.0.0.0" else a.host
        vals = []
        for x in a.args:
            try: vals.append(float(x) if ("." in x or "e" in x.lower()) else int(x))
            except ValueError: vals.append(x)
        SimpleUDPClient(host, a.port).send_message(a.addr, vals)
        print(f"  ⮞ OSC {host}:{a.port}  {a.addr} {vals}")
        sys.exit(0)
    n = [0]
    disp = Dispatcher()
    disp.set_default_handler(lambda addr, *args: (n.__setitem__(0, n[0]+1), print(f"  ⮜ {addr}  {list(args)}")))
    class _QuietServer(BlockingOSCUDPServer):
        def handle_error(self, request, client_address):
            pass  # ignore malformed / non-OSC datagrams instead of dumping a traceback
    srv = _QuietServer(("0.0.0.0", a.port), disp)
    print(f"👂 [OSC] listening on UDP 0.0.0.0:{a.port} for {a.timeout}s…")
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(a.timeout); srv.shutdown()
    print(f"✅ [OSC] received {n[0]} message(s).")
    sys.exit(0 if n[0] else 2)
