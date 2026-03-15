# workers/Command_Router/protocol_router/dispatch.py
#
# Logic for outbound message dispatch to transport managers.

import orjson
from .constants import LOCAL_DEBUG
from workers.logger.logger import router_logger

def dispatch_message(msg, managers):
    """
    Executes transport-specific publication based on the routing strategy.

    Inputs:
        msg (dict): The normalized message to dispatch.
        managers (dict): Dictionary of transport managers (mqtt, osc, etc).
    """
    strategy = msg.get("strategy", "")
    topic = msg["topic"]
    val = msg["val"]
    val_str = str(val)[:100] + ("..." if len(str(val)) > 100 else "")

    # --- MQTT Dispatch ---
    if "🚀" in strategy or "Ⓜ️" in strategy:
        mqtt_manager = managers.get("mqtt")
        if mqtt_manager and msg["source"] != "MQTT":
            payload = {
                "val": msg["val"], "source": msg.get("logical_source", msg["source"]),
                "ts": msg["ts"], "GUID": msg["guid"], "partition": msg["partition"]
            }
            if isinstance(msg.get("meta"), dict): payload.update(msg["meta"])
            try:
                mqtt_manager.publish(topic, orjson.dumps(payload).decode())
                router_logger.debug(f"📡📤📤 [OUTBOUND] MQTT >> {topic}: {val_str}")
            except Exception as e:
                router_logger.error(f"Ⓜ️🚫🛑 [ERROR] MQTT Publish Error: {e}")

    # --- OSC Dispatch ---
    if "🅾️" in strategy:
        osc_manager = managers.get("osc")
        if osc_manager and msg["source"] != "OSC":
            try:
                # The OSC manager expects a simple topic, not the full OPEN-AIR path
                osc_address = msg["meta"].get("osc_address", "/" + topic.replace("OPEN-AIR/", ""))
                osc_manager.send(osc_address, val)
                router_logger.debug(f"📡📤📤 [OUTBOUND] OSC >> {osc_address}: {val_str}")
            except Exception as e:
                router_logger.error(f"🅾️🚫🛑 [ERROR] OSC Dispatch Error: {e}")

    # --- MIDI Dispatch ---
    if "🎹" in strategy:
        midi_manager = managers.get("midi")
        if midi_manager and msg["source"] != "MIDI":
            try:
                midi_manager.publish(topic, val, msg["meta"])
                router_logger.debug(f"📡📤📤 [OUTBOUND] MIDI >> {topic}: {val_str}")
            except Exception as e:
                router_logger.error(f"🎹🚫🛑 [ERROR] MIDI Dispatch Error: {e}")

    # --- SNMP Dispatch ---
    if "Ⓢ" in strategy:
        snmp_manager = managers.get("snmp")
        if snmp_manager and msg["source"] != "SNMP":
            try:
                snmp_manager.publish(topic, val)
                router_logger.debug(f"📡📤📤 [OUTBOUND] SNMP >> {topic}: {val_str}")
            except Exception as e:
                router_logger.error(f"Ⓢ🚫🛑 [ERROR] SNMP Dispatch Error: {e}")

