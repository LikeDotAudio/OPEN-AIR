#!/usr/bin/env python3
"""Real WebSocket tester: connect, optionally send, print received frames.
    python3 Validations/Protocols/websocket/websocket_tester.py [--url ws://H:P] [--send MSG] [--timeout S]
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import argparse, time
from _proto_util import config  # noqa: E402
import websocket  # noqa: E402  (websocket-client)

if __name__ == "__main__":
    cfg, _ = config("websocket")
    default_url = f"ws://{cfg.get('host','127.0.0.1')}:{cfg.get('port','8080')}"
    ap = argparse.ArgumentParser(prog="websocket_tester")
    ap.add_argument("--url", default=default_url)
    ap.add_argument("--send")
    ap.add_argument("--timeout", type=float, default=10.0)
    a = ap.parse_args()
    print(f"🔌 [WS] connecting to {a.url}…")
    try:
        ws = websocket.create_connection(a.url, timeout=a.timeout)
    except Exception as e:
        print(f"❌ [WS] connect failed: {e}"); sys.exit(1)
    print("✅ [WS] connected.")
    if a.send:
        ws.send(a.send); print(f"  ⮞ {a.send}")
    ws.settimeout(a.timeout); n = 0; end = time.time() + a.timeout
    try:
        while time.time() < end:
            try: msg = ws.recv()
            except websocket.WebSocketTimeoutException: break
            if msg == "": break
            n += 1; print(f"  ⮜ {str(msg)[:300]}")
    finally:
        ws.close()
    print(f"✅ [WS] received {n} frame(s)."); sys.exit(0)
