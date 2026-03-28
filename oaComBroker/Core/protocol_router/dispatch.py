# protocol_router/dispatch.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Logic for outbound message dispatch to transport managers.

import orjson
from .constants import LOCAL_DEBUG, app_constants
from oaLogging.Core.logger import router_logger
from oaOchestration.Managers.protocol_guard import protocol_guard

def dispatch_message(msg, managers):
    """
    Executes transport-specific publication based on the routing strategy.
    Cleaned up to use protocol guards for error handling.
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
        if osc_manager and msg["source"] != "OSC" and msg.get("logical_source") != "OSC":
            _dispatch_osc(osc_manager, topic, val, msg, val_str)

    # --- MIDI Dispatch ---
    if "🎹" in strategy:
        midi_manager = managers.get("midi")
        if midi_manager and msg["source"] != "MIDI" and msg.get("logical_source") != "MIDI":
            _dispatch_midi(midi_manager, topic, val, msg, val_str)

    # --- SNMP Dispatch ---
    if "Ⓢ" in strategy:
        snmp_manager = managers.get("snmp")
        if snmp_manager and msg["source"] != "SNMP" and msg.get("logical_source") != "SNMP":
            _dispatch_snmp(snmp_manager, topic, val, val_str)

@protocol_guard("MQTT")
def _dispatch_mqtt(mqtt_manager, topic, msg, val_str):
    payload = {
        "val": msg["val"], "source": msg.get("logical_source", msg["source"]),
        "ts": msg["ts"], "GUID": msg["guid"], "partition": msg["partition"]
    }
    if isinstance(msg.get("meta"), dict): payload.update(msg["meta"])
    
    # --- Namespace Split: Publish to TX namespace ---
    tx_topic = topic
    from .constants import app_constants
    base = app_constants.MQTT_BASE_TOPIC
    if base in topic and f"{base}/Cmd/" not in topic and f"{base}/Tx/" not in topic:
        tx_topic = topic.replace(base, f"{base}/Tx")
        
    mqtt_manager.publish(tx_topic, orjson.dumps(payload).decode())
    router_logger.debug(f"📡📤📤 [OUTBOUND] MQTT >> {tx_topic}: {val_str}")

@protocol_guard("OSC")
def _dispatch_osc(osc_manager, topic, val, msg, val_str):
    osc_address = msg["meta"].get("osc_address", "/" + topic.replace("OPEN-AIR/", ""))
    osc_manager.send(osc_address, val)
    router_logger.debug(f"📡📤📤 [OUTBOUND] OSC >> {osc_address}: {val_str}")

@protocol_guard("MIDI")
def _dispatch_midi(midi_manager, topic, val, msg, val_str):
    midi_manager.publish(topic, val, msg["meta"])
    router_logger.debug(f"📡📤📤 [OUTBOUND] MIDI >> {topic}: {val_str}")

@protocol_guard("SNMP")
def _dispatch_snmp(snmp_manager, topic, val, val_str):
    snmp_manager.publish(topic, val)
    router_logger.debug(f"📡📤📤 [OUTBOUND] SNMP >> {topic}: {val_str}")
