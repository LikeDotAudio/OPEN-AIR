# Core/protocol_router/dispatch.py
#
# Logic for outbound message dispatch to protocol-specific transport managers.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260330.1600.1

import orjson
from .constants import LOCAL_DEBUG, app_constants
from oaLogging.Methods.matrix_gate import matrix_log
from oaOchestration.Managers.protocol_guard import protocol_guard

def dispatch_message(msg, managers):
    """
    Executes transport-specific publication based on the routing strategy.
    """
    strategy = msg.get("strategy", "")
    topic = msg["topic"]
    val = msg["val"]
    val_str = str(val)[:100] + ("..." if len(str(val)) > 100 else "")

    # --- MQTT Dispatch ---
    if "🚀" in strategy or "Ⓜ️" in strategy:
        mqtt_manager = managers.get("mqtt")
        if mqtt_manager and msg["source"] != "MQTT" and msg.get("logical_source") != "MQTT":
            _dispatch_mqtt(mqtt_manager, topic, msg, val_str)

    # --- OSC Dispatch ---
    if "🅾️" in strategy:
        osc_manager = managers.get("osc")
        if osc_manager and msg["source"] not in ["OSC", "OSC-TX"] and msg.get("logical_source") not in ["OSC", "OSC-TX"]:
            _dispatch_osc(osc_manager, topic, val, msg, val_str)

    # --- MIDI Dispatch ---
    if "🎹" in strategy:
        midi_manager = managers.get("midi")
        if midi_manager and msg["source"] not in ["MIDI", "MIDI-TX"] and msg.get("logical_source") not in ["MIDI", "MIDI-TX"]:
            _dispatch_midi(midi_manager, topic, val, msg, val_str)

    # --- SNMP Dispatch ---
    if "Ⓢ" in strategy:
        snmp_manager = managers.get("snmp")
        if snmp_manager and msg["source"] not in ["SNMP", "SNMP-TX"] and msg.get("logical_source") not in ["SNMP", "SNMP-TX"]:
            _dispatch_snmp(snmp_manager, topic, val, val_str)

    # --- SMPTE 2138 Dispatch ---
    # We use the 🔗 emoji or explicit flag if needed. 
    # For now, we dispatch if it's an Action strategy.
    if "🔗" in strategy or "🚀" in strategy:
        smpte_manager = managers.get("smpte2138")
        if smpte_manager and msg["source"] != "SMPTE2138" and msg.get("logical_source") != "SMPTE2138":
            _dispatch_smpte2138(smpte_manager, topic, val, msg, val_str)

@protocol_guard("MQTT")
def _dispatch_mqtt(mqtt_manager, topic, msg, val_str):
    payload = {
        "val": msg["val"], "source": msg.get("logical_source", msg["source"]),
        "ts": msg["ts"], "GUID": msg["guid"], "partition": msg["partition"]
    }
    if isinstance(msg.get("meta"), dict): payload.update(msg["meta"])
    
    tx_topic = topic
    base = app_constants.MQTT_BASE_TOPIC
    if base in topic and f"{base}/Cmd/" not in topic and f"{base}/Tx/" not in topic:
        tx_topic = topic.replace(base, f"{base}/Tx")
        
    # ⚡ OPTIMIZATION: Retain status and monitor topics for late-joining observers
    retain = ("/Status/" in topic or "/Monitor/" in topic)
    
    try:
        encoded_payload = orjson.dumps(payload).decode()
    except Exception as e:
        matrix_log("core", "router", "_dispatch_mqtt", f"❌ [ERROR] Failed to serialize MQTT payload for {topic}: {e}", "ERROR")
        return

    mqtt_manager.publish(tx_topic, encoded_payload, retain=retain)
    matrix_log("core", "router", "_dispatch_mqtt", f"📡📤📤 [OUTBOUND] MQTT >> {tx_topic} (Retain={retain}): {val_str}", "DEBUG")

@protocol_guard("OSC")
def _dispatch_osc(osc_manager, topic, val, msg, val_str):
    osc_address = msg["meta"].get("osc_address", "/" + topic.replace("OPEN-AIR/", ""))
    osc_manager.send(osc_address, val)
    matrix_log("core", "router", "_dispatch_osc", f"📡📤📤 [OUTBOUND] OSC >> {osc_address}: {val_str}", "DEBUG")

@protocol_guard("MIDI")
def _dispatch_midi(midi_manager, topic, val, msg, val_str):
    midi_manager.publish(topic, val, msg["meta"])
    matrix_log("core", "router", "_dispatch_midi", f"📡📤📤 [MIDI] >> {topic}: {val_str}", "DEBUG")

@protocol_guard("SNMP")
def _dispatch_snmp(snmp_manager, topic, val, val_str):
    snmp_manager.publish(topic, val)
    matrix_log("core", "router", "_dispatch_snmp", f"📡📤📤 [SNMP] >> {topic}: {val_str}", "DEBUG")

@protocol_guard("SMPTE2138")
def _dispatch_smpte2138(smpte_manager, topic, val, msg, val_str):
    """Routes normalized internal actions to the SMPTE 2138 bridge."""
    # The manager's ingest method handles OID mapping and Protobuf encoding.
    smpte_manager.handle_router_event(topic, val, msg.get("meta", {}))
    matrix_log("core", "router", "_dispatch_smpte2138", f"📡📤📤 [SMPTE2138] >> {topic}: {val_str}", "DEBUG")
