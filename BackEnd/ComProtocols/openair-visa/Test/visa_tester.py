# ==========================================
# Header: visa_tester.py
# Purpose: visa_tester.py implementation.
# Description: Logic and implementation for visa_tester.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

#!/usr/bin/env python3
"""Real VISA tester: list instruments, or open a resource and query *IDN?.
    python3 Validations/Protocols/visa/visa_tester.py list
    python3 Validations/Protocols/visa/visa_tester.py idn [--resource RSRC]
"""
import pathlib, sys
import os

# Locate the shared protocol-test helpers relative to this file rather than an
# absolute path. This file is BackEnd/ComProtocols/openair-visa/Test/, so the
# repo root is four parents up; the helpers moved to TESTS/Protocols/.
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT / "TESTS" / "Protocols"))
import argparse
from _proto_util import config  # noqa: E402
import pyvisa  # noqa: E402

if __name__ == "__main__":
    cfg, _ = config("visa")
    ap = argparse.ArgumentParser(prog="visa_tester")
    ap.add_argument("action", nargs="?", default="list", choices=["list", "idn", "publish"])
    ap.add_argument("--resource", default=cfg.get("resource", ""))
    ap.add_argument("--timeout", type=int, default=int(cfg.get("timeout_ms", 5000)))
    a = ap.parse_args()
    try:
        import openair_visa
        rm = openair_visa.ResourceManager()
        print("🔧 [VISA] Using Rust backend (openair_visa)")
    except ImportError:
        try:
            import pyvisa
            rm = pyvisa.ResourceManager("@py")
            print("🔧 [VISA] Using PyVISA (@py) backend")
        except Exception:
            import pyvisa
            rm = pyvisa.ResourceManager()
            print("🔧 [VISA] Using PyVISA backend")
    res = list(rm.list_resources())
    print(f"\n🔎 [VISA] Found {len(res)} resource(s). Probing each for *IDN? ...\n")
    print("=" * 130)
    print(f"{'RESOURCE':<35} | {'RAW *IDN? RESPONSE':<50} | {'KNOWN DEVICE TYPE':<35}")
    print("-" * 130)
    
    if a.action == "publish":
        print(f"🚀 [VISA-MQTT] Starting native Rust MQTT publisher agent to 127.0.0.1:1883...")
        if hasattr(rm, "scan_and_publish_mqtt"):
            try:
                rm.scan_and_publish_mqtt("127.0.0.1", 1883)
                print("✅ [VISA-MQTT] Scan and Publish complete!")
            except Exception as e:
                print(f"❌ [VISA-MQTT] Failed: {e}")
        else:
            print("❌ [VISA-MQTT] Rust backend required for MQTT publishing.")
        sys.exit(0)
    
    if a.action == "list":
        device_infos = []
        for target in res:
            if hasattr(rm, "identify_device"):
                try:
                    info = rm.identify_device(target)
                    device_infos.append(info)
                    raw_idn = info.get("raw_idn", "")
                    dtype = info.get("device_type", "Unknown")
                    res_trunc = (target[:32] + '...') if len(target) > 32 else target
                    raw_idn_trunc = (raw_idn[:47] + '...') if len(raw_idn) > 47 else raw_idn
                    dtype_trunc = (dtype[:29] + '...') if len(dtype) > 29 else dtype
                    
                    if raw_idn.strip():
                        print(f"✅ {res_trunc:<33} | {raw_idn_trunc:<50} | 🏷️  {dtype_trunc:<32}")
                    else:
                        print(f"❌ {res_trunc:<33} | {'<No Response / Timeout>':<50} | ⚠️  {dtype_trunc:<32}")
                    sys.stdout.flush()
                except Exception as e:
                    res_trunc = (target[:32] + '...') if len(target) > 32 else target
                    print(f"❌ {res_trunc:<33} | {'<Connection Failed>':<50} | ⚠️  Error")
                    sys.stdout.flush()
            else:
                try:
                    inst = rm.open_resource(target)
                    inst.timeout = 1000
                    idn = inst.query("*IDN?").strip()
                    res_trunc = (target[:32] + '...') if len(target) > 32 else target
                    idn_trunc = (idn[:47] + '...') if len(idn) > 47 else idn
                    print(f"✅ {res_trunc:<33} | {idn_trunc:<50} | ")
                    sys.stdout.flush()
                    inst.close()
                except Exception:
                    print(f"❌ {target:<33} | {'<No Response>':<50} | ")
                    sys.stdout.flush()
                    
        print("=" * 130)
        
        print("\n🚀 PUBLISHING CONNECTION TO DETAILS TO MQTT:   [VISA] Using Rust backend (openair_visa)")
        if hasattr(rm, "publish_devices_mqtt"):
            try:
                import configparser
                import os
                local_cfg = configparser.ConfigParser()
                ini_path = os.path.join(os.path.dirname(__file__), "..", "config.ini")
                local_cfg.read(ini_path)
                try:
                    base_topic = local_cfg.get("visa", "topic_device")
                except (configparser.NoSectionError, configparser.NoOptionError):
                    base_topic = cfg.get("topic_device", "OpenAir/System/Protocols/visa/Device")
                
                rm.publish_devices_mqtt("127.0.0.1", 1883, device_infos, base_topic)
                print("✅ [VISA-MQTT] Publish complete!")
                sys.stdout.flush()
                
                # --- Start MQTT Daemon FIRST ---
                import time
                print("\n🚀 Starting MQTT Write/Read daemon...")
                print(f"   📡 Subscribing to: {base_topic}/+/+/+/Write")
                openair_visa.start_mqtt_daemon("127.0.0.1", 1883, base_topic)
                print("✅ [VISA-MQTT] Daemon running!")
                sys.stdout.flush()
                time.sleep(1)  # Let daemon subscribe
                
                # --- Set up MQTT test client to send commands ---
                import paho.mqtt.client as mqtt
                
                read_results = {}
                
                def on_message(client, userdata, msg):
                    read_results[msg.topic] = msg.payload.decode().strip()
                
                mqttc = mqtt.Client(client_id="openair-visa-tester", protocol=mqtt.MQTTv311)
                mqttc.on_message = on_message
                mqttc.connect("127.0.0.1", 1883, 60)
                mqttc.subscribe(f"{base_topic}/+/+/+/Read")
                mqttc.loop_start()
                
                # Build device -> topic mapping for online devices
                counts = {}
                device_topics = []
                for info in device_infos:
                    raw_idn = info.get("raw_idn", "")
                    if raw_idn.strip():
                        cat = info.get("device_type", "Unknown").replace(" ", "_")
                        model = info.get("model", "Unknown").replace(" ", "_")
                        resource = info.get("resource", "")
                        key = (cat, model)
                        count = counts.get(key, 0)
                        counts[key] = count + 1
                        topic_prefix = f"{base_topic.rstrip('/')}/{cat}/{model}/Dev{count}"
                        device_topics.append((resource, topic_prefix))
                
                # --- Reset all online devices via MQTT Write ---
                print("\n🔄 Resetting all online devices via MQTT...")
                for resource, topic_prefix in device_topics:
                    write_topic = f"{topic_prefix}/Write"
                    print(f"   📡 [MQTT] -> *RST to {write_topic}")
                    mqttc.publish(write_topic, "*RST", qos=1)
                sys.stdout.flush()
                
                print("\n⏳ Waiting 5 seconds after reset...")
                time.sleep(5)
                
                # --- Check status via MQTT Write (queries end with ?) ---
                print("\n📊 Checking device status via MQTT Write/Read...")
                for resource, topic_prefix in device_topics:
                    write_topic = f"{topic_prefix}/Write"
                    read_topic = f"{topic_prefix}/Read"
                    
                    # Send *STB? query
                    print(f"   📡 [MQTT] -> *STB? to {write_topic}")
                    read_results.pop(read_topic, None)
                    mqttc.publish(write_topic, "*STB?", qos=1)
                    time.sleep(2)
                    
                    stb = read_results.get(read_topic, "<No Response>")
                    print(f"      STB: {stb}")
                    
                    # Send :SYST:ERR? query
                    print(f"   📡 [MQTT] -> :SYST:ERR? to {write_topic}")
                    read_results.pop(read_topic, None)
                    mqttc.publish(write_topic, ":SYST:ERR?", qos=1)
                    time.sleep(2)
                    
                    err = read_results.get(read_topic, "<No Response>")
                    print(f"      ERR: {err}")
                sys.stdout.flush()
                
                # --- Switch to live monitoring mode ---
                # Re-subscribe to both Write and Read for all devices
                mqttc.subscribe(f"{base_topic}/+/+/+/Write")
                mqttc.subscribe(f"{base_topic}/+/+/+/Read")
                
                def on_live_message(client, userdata, msg):
                    topic = msg.topic
                    payload = msg.payload.decode().strip()
                    if not payload:
                        return
                    if topic.endswith("/Write"):
                        print(f"   📥 [WRITE IN]  {topic}  ←  \"{payload}\"")
                    elif topic.endswith("/Read"):
                        print(f"   📤 [READ OUT]  {topic}  →  \"{payload}\"")
                    sys.stdout.flush()
                
                mqttc.on_message = on_live_message
                
                print("\n✅ All commands sent via MQTT Write/Read pipeline!")
                print("   💡 Publish a SCPI command to .../DevN/Write to send it to the device.")
                print("   💡 If the command ends with '?', the response appears in .../DevN/Read.")
                print("\n👁️  Live monitoring Write/Read activity. Press Ctrl+C to stop.\n")
                sys.stdout.flush()
                try:
                    import signal
                    signal.pause()
                except KeyboardInterrupt:
                    print("\n🛑 Daemon stopped by user.")
                    mqttc.loop_stop()
                    mqttc.disconnect()
                # -----------------------------------------------------------
                
            except Exception as e:
                print(f"❌ [VISA-MQTT] Failed: {e}")
                sys.stdout.flush()
        else:
            print("❌ [VISA-MQTT] Rust backend required for MQTT publishing.")
            sys.stdout.flush()
            
        sys.stdout.flush()
        os._exit(0 if res else 2)
    target = a.resource or (res[0] if res else None)
    if not target:
        print("❌ [VISA] no resource to query (specify --resource)."); sys.stdout.flush(); os._exit(1)
    print(f"🔌 [VISA] opening {target} …")
    try:
        inst = rm.open_resource(target); inst.timeout = a.timeout
        print(f"  ⮜ *IDN? -> {inst.query('*IDN?').strip()}")
        inst.close()
    except Exception as e:
        print(f"❌ [VISA] query failed: {e}"); sys.stdout.flush(); os._exit(2)
    sys.stdout.flush()
    os._exit(0)
