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

def dispatch_message(msg, managers, enablement=None, topic_routing=None, is_active=True):
    """
    Executes transport-specific publication based on the routing strategy.
    """
    matrix = enablement or {}
    t_routing = topic_routing or {}
    
    # Normalize Source Name for Matrix Lookup
    src_raw = str(msg["source"]).upper()
    src = src_raw.replace("-TX", "") if "-TX" in src_raw else src_raw
    
    strategy = msg.get("strategy", "")
    topic = msg["topic"]
    val = msg["val"]
    val_str = str(val)[:100] + ("..." if len(str(val)) > 100 else "")

    # Helper to resolve topic override or prefixing
    def get_topic(dest):
        cfg = t_routing.get((src, dest))
        if cfg and cfg.get("send"):
            prefix = cfg["send"]
            if str(topic).startswith(prefix):
                return topic
            # If it's a prefix, we append the topic (removing existing OPEN-AIR/ if redundant)
            suffix = topic.replace("OPEN-AIR/", "")
            return f"{prefix.rstrip('/')}/{suffix.lstrip('/')}"
        return topic

    # --- MQTT Dispatch ---
    if "🚀" in strategy or "Ⓜ️" in strategy:
        if is_active and matrix.get(src, {}).get("MQTT", True):
            mqtt_manager = managers.get("mqtt")
            if mqtt_manager and msg["source"] != "MQTT" and msg.get("logical_source") != "MQTT":
                _dispatch_mqtt(mqtt_manager, get_topic("MQTT"), msg, val_str)

    # --- OSC Dispatch ---
    if "🅾️" in strategy:
        if is_active and matrix.get(src, {}).get("OSC", True):
            osc_manager = managers.get("osc")
            if osc_manager and msg["source"] not in ["OSC", "OSC-TX"] and msg.get("logical_source") not in ["OSC", "OSC-TX"]:
                _dispatch_osc(osc_manager, get_topic("OSC"), val, msg, val_str)

    # --- MIDI Dispatch ---
    if "🎹" in strategy:
        if is_active and matrix.get(src, {}).get("MIDI", True):
            midi_manager = managers.get("midi")
            if midi_manager and msg["source"] not in ["MIDI", "MIDI-TX"] and msg.get("logical_source") not in ["MIDI", "MIDI-TX"]:
                _dispatch_midi(midi_manager, get_topic("MIDI"), val, msg, val_str)

    # --- SNMP Dispatch ---
    if "Ⓢ" in strategy:
        if is_active and matrix.get(src, {}).get("SNMP", True):
            snmp_manager = managers.get("snmp")
            if snmp_manager and msg["source"] not in ["SNMP", "SNMP-TX"] and msg.get("logical_source") not in ["SNMP", "SNMP-TX"]:
                _dispatch_snmp(snmp_manager, get_topic("SNMP"), val, val_str)

    # --- NMOS Dispatch ---
    if "N" in strategy or "NMOS" in strategy:
        if is_active and matrix.get(src, {}).get("NMOS", True):
            nmos_manager = managers.get("nmos")
            if nmos_manager and msg["source"] != "NMOS" and msg.get("logical_source") != "NMOS":
                _dispatch_nmos(nmos_manager, get_topic("NMOS"), val, msg, val_str)

    # --- SMPTE 2138 Dispatch ---
    if "🔗" in strategy or "🚀" in strategy:
        if is_active and matrix.get(src, {}).get("SMPTE2138", True):
            smpte_manager = managers.get("smpte2138")
            if smpte_manager and msg["source"] != "SMPTE2138" and msg.get("logical_source") != "SMPTE2138":
                _dispatch_smpte2138(smpte_manager, get_topic("SMPTE2138"), val, msg, val_str)

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
        if app_constants.ROUTER_DISPATCH_LOGS:
            matrix_log("comms", "broker", "_dispatch_mqtt", f"❌ [ERROR] Failed to serialize MQTT payload for {topic}: {e}", "ERROR")
        return

    mqtt_manager.publish(tx_topic, encoded_payload, retain=retain)
    if app_constants.ROUTER_DISPATCH_LOGS:
        matrix_log("comms", "broker", "_dispatch_mqtt", f"📡📤📤 [OUTBOUND] MQTT >> {tx_topic} (Retain={retain}): {val_str}", "DEBUG")

@protocol_guard("OSC")
def _dispatch_osc(osc_manager, topic, val, msg, val_str):
    osc_address = msg["meta"].get("osc_address", "/" + topic.replace("OPEN-AIR/", ""))
    
    # ⚡ RESILIENCE: Handle complex GUI-sourced payloads
    if isinstance(val, dict) and "val" in val:
        payload = val["val"]
    else:
        payload = val
        
    osc_manager.send(osc_address, payload)
    if app_constants.ROUTER_DISPATCH_LOGS:
        matrix_log("comms", "broker", "_dispatch_osc", f"📡📤📤 [OUTBOUND] OSC >> {osc_address}: {val_str}", "DEBUG")

@protocol_guard("MIDI")
def _dispatch_midi(midi_manager, topic, val, msg, val_str):
    midi_manager.publish(topic, val, msg["meta"])
    if app_constants.ROUTER_DISPATCH_LOGS:
        matrix_log("comms", "broker", "_dispatch_midi", f"📡📤📤 [MIDI] >> {topic}: {val_str}", "DEBUG")

@protocol_guard("SNMP")
def _dispatch_snmp(snmp_manager, topic, val, val_str):
    snmp_manager.publish(topic, val)
    if app_constants.ROUTER_DISPATCH_LOGS:
        matrix_log("comms", "broker", "_dispatch_snmp", f"📡📤📤 [SNMP] >> {topic}: {val_str}", "DEBUG")

@protocol_guard("NMOS")
def _dispatch_nmos(nmos_manager, topic, val, msg, val_str):
    """Routes normalized internal actions to the NMOS IS-07 bridge."""
    nmos_manager.handle_router_event(topic, val, msg.get("meta", {}))
    if app_constants.ROUTER_DISPATCH_LOGS:
        matrix_log("comms", "broker", "_dispatch_nmos", f"📡📤📤 [NMOS] >> {topic}: {val_str}", "DEBUG")

@protocol_guard("SMPTE2138")
def _dispatch_smpte2138(smpte_manager, topic, val, msg, val_str):
    """Routes normalized internal actions to the SMPTE 2138 bridge."""
    # The manager's ingest method handles OID mapping and Protobuf encoding.
    smpte_manager.handle_router_event(topic, val, msg.get("meta", {}))
    if app_constants.ROUTER_DISPATCH_LOGS:
        matrix_log("comms", "broker", "_dispatch_smpte2138", f"📡📤📤 [SMPTE2138] >> {topic}: {val_str}", "DEBUG")
