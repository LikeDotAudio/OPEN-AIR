# ==========================================
# Header: mqtt_tester.py
# Purpose: mqtt_tester.py implementation.
# Description: Logic and implementation for mqtt_tester.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

#!/usr/bin/env python3
"""Real MQTT tester: subscribe to the broker and print messages (the bus itself).
    python3 Validations/Protocols/mqtt/mqtt_tester.py [--topic '#'] [--timeout S] [--broker H] [--port N]
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import argparse, time
from _proto_util import config  # noqa: E402

if __name__ == "__main__":
    cfg, _ = config("mqtt")
    ap = argparse.ArgumentParser(prog="mqtt_tester")
    ap.add_argument("--broker", default=cfg.get("host", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(cfg.get("tcp_port", 1883)))
    ap.add_argument("--topic", default="#")
    ap.add_argument("--timeout", type=float, default=15.0)
    a = ap.parse_args()
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        print("❌ paho-mqtt not installed (pip install paho-mqtt)"); sys.exit(1)
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except (AttributeError, TypeError):
        client = mqtt.Client()
    n = [0]
    def on_message(c, u, m):
        n[0] += 1
        print(f"  ⮜ {m.topic}  {m.payload.decode('utf-8','replace')[:300]}")
    client.on_message = on_message
    print(f"👂 [MQTT] {a.broker}:{a.port} topic '{a.topic}' for {a.timeout}s…")
    try:
        client.connect(a.broker, a.port, keepalive=max(10, int(a.timeout)+5))
    except Exception as e:
        print(f"❌ [MQTT] connect failed: {e} (is mosquitto running?)"); sys.exit(1)
    client.subscribe(a.topic)
    client.loop_start(); time.sleep(a.timeout); client.loop_stop(); client.disconnect()
    print(f"✅ [MQTT] {n[0]} message(s).")
    sys.exit(0 if n[0] else 2)
