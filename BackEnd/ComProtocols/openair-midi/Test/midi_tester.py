# ==========================================
# Header: midi_tester.py
# Purpose: midi_tester.py implementation.
# Description: Logic and implementation for midi_tester.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

#!/usr/bin/env python3
"""
MIDI Tester Script for OPEN-AIR
Tests the rust backend (oamidiengine_rs) MIDI engine.
"""
import sys
import os
import time
import argparse

sys.path.insert(0, "/home/anthony/Documents/OPEN-AIR/BackEnd")
try:
    from Core import oaRustCore
    # Or specifically
    import oamidiengine_rs
except ImportError:
    pass # Will handle gracefully below

# Inline comment: Logic for main
def main():
    ap = argparse.ArgumentParser(prog="midi_tester")
    ap.add_argument("action", nargs="?", default="daemon", choices=["list", "listen", "publish", "daemon"])
    ap.add_argument("--port", type=int, default=0, help="Port index to listen to")
    a = ap.parse_args()

    try:
        import oamidiengine_rs
        engine = oamidiengine_rs.MidiEngine()
        print("🔧 [MIDI] Using Rust backend (oamidiengine_rs)")
    except ImportError as e:
        print(f"❌ [MIDI] Could not import Rust MIDI backend: {e}")
        sys.exit(1)

    print("\n🔎 [MIDI] Inputs:")
    inputs = engine.list_inputs()
    for i, name in enumerate(inputs):
        print(f"   [{i}] {name}")

    print("\n🔎 [MIDI] Outputs:")
    outputs = engine.list_outputs()
    for i, name in enumerate(outputs):
        print(f"   [{i}] {name}")

    if a.action == "publish":
        print("\n🚀 [MIDI-MQTT] Publishing discovered devices to MQTT...")
        import configparser
        cfg = configparser.ConfigParser()
        ini_path = os.path.join(os.path.dirname(__file__), "..", "config.ini")
        cfg.read(ini_path)
        base_topic = cfg.get("midi", "topic_device", fallback="OpenAir/System/Protocols/midi/Device")
        
        try:
            engine.publish_devices_mqtt("127.0.0.1", 1883, base_topic)
            print("✅ [MIDI-MQTT] Publish complete!")
        except Exception as e:
            print(f"❌ [MIDI-MQTT] Publish failed: {e}")
        
        sys.exit(0)

    if a.action == "listen":
        if not inputs:
            print("\n❌ No inputs to listen to.")
            sys.exit(1)
        
        if a.port >= len(inputs):
            print(f"\n❌ Port index {a.port} is out of range.")
            sys.exit(1)

        print(f"\n🎧 [MIDI] Opening input port {a.port} ({inputs[a.port]})...")
        engine.open_input(a.port)
        
        print("   Listening for events... (Press Ctrl+C to stop)")
        try:
            while True:
                events = engine.get_buffered_events()
                for ev in events:
                    print(f"   📥 [MIDI IN] timestamp: {ev['timestamp']}, data: {list(ev['data'])}")
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("\n🛑 Stopped listening.")
        finally:
            engine.close()

    if a.action == "daemon":
        if not inputs:
            print("\n❌ No inputs to listen to.")
            sys.exit(1)
        
        if a.port >= len(inputs):
            print(f"\n❌ Port index {a.port} is out of range.")
            sys.exit(1)

        import configparser
        import json
        try:
            import paho.mqtt.client as mqtt
            from paho.mqtt.enums import CallbackAPIVersion
        except ImportError:
            print("❌ Please install paho-mqtt: pip install paho-mqtt")
            sys.exit(1)

        # Auto-detect physical port if user didn't explicitly specify one
        target_port = a.port
        if len(sys.argv) == 1 and len(inputs) > 1 and "Through" in inputs[0]:
            target_port = 1

        cfg = configparser.ConfigParser()
        ini_path = os.path.join(os.path.dirname(__file__), "..", "config.ini")
        cfg.read(ini_path)
        base_topic = cfg.get("midi", "topic_device", fallback="OpenAir/System/Protocols/midi/Device")

        client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2, client_id=f"midi-tester-{os.getpid()}")
        client.connect("127.0.0.1", 1883, 60)
        client.loop_start()

        print(f"\n🎧 [MIDI DAEMON] Opening input port {target_port} ({inputs[target_port]})...")
        engine.open_input(target_port)
        
        print(f"   Listening for events and publishing to {base_topic}/Input/Dev{target_port}/... (Press Ctrl+C to stop)")
        try:
            while True:
                events = engine.get_buffered_events()
                for ev in events:
                    raw_data = list(ev['data'])
                    if len(raw_data) >= 1:
                        status = raw_data[0]
                        channel = (status & 0x0F) + 1
                        command = status & 0xF0
                        
                        data1 = raw_data[1] if len(raw_data) > 1 else 0
                        data2 = raw_data[2] if len(raw_data) > 2 else 0
                        
                        subtopic = ""
                        payload_val = 0
                        
                        if command == 128:
                            subtopic = f"Channel{channel}/Note/{data1}"
                            payload_val = 0
                        elif command == 144:
                            subtopic = f"Channel{channel}/Note/{data1}"
                            payload_val = data2
                        elif command == 176:
                            subtopic = f"Channel{channel}/ControlChange/{data1}"
                            payload_val = data2
                        elif command == 192:
                            subtopic = f"Channel{channel}/ProgramChange"
                            payload_val = data1
                        elif command == 224:
                            subtopic = f"Channel{channel}/PitchBend"
                            payload_val = (data2 << 7) | data1
                        else:
                            subtopic = f"Channel{channel}/Raw/{command}"
                            payload_val = data1
                            
                        print(f"   📥 [MIDI IN] raw: {raw_data}")
                        topic = f"{base_topic}/Input/Dev{target_port}/{subtopic}"
                        print(f"   📡 [MQTT PUB] {topic} = {payload_val}")
                        client.publish(topic, str(payload_val))
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("\n🛑 Stopped listening.")
        finally:
            engine.close()
            client.loop_stop()
            client.disconnect()

if __name__ == "__main__":
    main()
