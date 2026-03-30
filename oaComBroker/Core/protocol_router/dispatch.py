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
# Version 20260328.1415.1
#
# Description:
# This module implements the egress logic for the ProtocolRouter. It interprets
# the emoji-based strategy strings calculated during ingestion and routes the
# normalized message payloads to the appropriate transport managers (MQTT, OSC,
# MIDI, SNMP).
#
# Architectural Role:
# - Acts as the final stage of the ProtocolRouter pipeline.
# - Enforces loop prevention by checking the origin source before dispatch.
# - Utilizes @protocol_guard decorators to ensure transport-level isolation.

import orjson
from .constants import LOCAL_DEBUG, app_constants
from oaLogging.Core.logger import router_logger
from oaOchestration.Managers.protocol_guard import protocol_guard

def dispatch_message(msg, managers):
    """
    Executes transport-specific publication based on the routing strategy.
    
    Args:
        msg (dict): The normalized message packet.
        managers (dict): Map of active protocol managers.
        
    Side Effects:
        - Triggers network I/O via registered managers.
        - Logs outbound activity to the router_logger.
    """
    strategy = msg.get("strategy", "")
    topic = msg["topic"]
    val = msg["val"]
    val_str = str(val)[:100] + ("..." if len(str(val)) > 100 else "")

    # --- MQTT Dispatch: Broadcasts state to the network ---
    if "🚀" in strategy or "Ⓜ️" in strategy:
        mqtt_manager = managers.get("mqtt")
        # Prevent reflection: Do not send back to the source transport.
        if mqtt_manager and msg["source"] != "MQTT" and msg.get("logical_source") != "MQTT":
            _dispatch_mqtt(mqtt_manager, topic, msg, val_str)

    # --- OSC Dispatch: Routes to external control surfaces ---
    if "🅾️" in strategy:
        osc_manager = managers.get("osc")
        if osc_manager and msg["source"] != "OSC" and msg.get("logical_source") != "OSC":
            _dispatch_osc(osc_manager, topic, val, msg, val_str)

    # --- MIDI Dispatch: Routes to physical hardware controllers ---
    if "🎹" in strategy:
        midi_manager = managers.get("midi")
        if midi_manager and msg["source"] != "MIDI" and msg.get("logical_source") != "MIDI":
            _dispatch_midi(midi_manager, topic, val, msg, val_str)

    # --- SNMP Dispatch: Routes to network infrastructure ---
    if "Ⓢ" in strategy:
        snmp_manager = managers.get("snmp")
        if snmp_manager and msg["source"] != "SNMP" and msg.get("logical_source") != "SNMP":
            _dispatch_snmp(snmp_manager, topic, val, val_str)

@protocol_guard("MQTT")
def _dispatch_mqtt(mqtt_manager, topic, msg, val_str):
    """Encapsulates the MQTT-specific publication logic."""
    payload = {
        "val": msg["val"], "source": msg.get("logical_source", msg["source"]),
        "ts": msg["ts"], "GUID": msg["guid"], "partition": msg["partition"]
    }
    if isinstance(msg.get("meta"), dict): payload.update(msg["meta"])
    
    # --- Namespace Split: Publish to TX (Transmit) namespace ---
    tx_topic = topic
    base = app_constants.MQTT_BASE_TOPIC
    if base in topic and f"{base}/Cmd/" not in topic and f"{base}/Tx/" not in topic:
        tx_topic = topic.replace(base, f"{base}/Tx")
        
    mqtt_manager.publish(tx_topic, orjson.dumps(payload).decode())
    if LOCAL_DEBUG:
        router_logger.debug(f"📡📤📤 [OUTBOUND] MQTT >> {tx_topic}: {val_str}")

@protocol_guard("OSC")
def _dispatch_osc(osc_manager, topic, val, msg, val_str):
    """Encapsulates the OSC-specific publication logic."""
    osc_address = msg["meta"].get("osc_address", "/" + topic.replace("OPEN-AIR/", ""))
    osc_manager.send(osc_address, val)
    if LOCAL_DEBUG:
        router_logger.debug(f"📡📤📤 [OUTBOUND] OSC >> {osc_address}: {val_str}")

@protocol_guard("MIDI")
def _dispatch_midi(midi_manager, topic, val, msg, val_str):
    """Encapsulates the MIDI-specific publication logic."""
    midi_manager.publish(topic, val, msg["meta"])
    if LOCAL_DEBUG:
        router_logger.debug(f"📡📤📤 [MIDI] >> {topic}: {val_str}")

@protocol_guard("SNMP")
def _dispatch_snmp(snmp_manager, topic, val, val_str):
    """Encapsulates the SNMP-specific publication logic."""
    snmp_manager.publish(topic, val)
    if LOCAL_DEBUG:
        router_logger.debug(f"📡📤📤 [SNMP] >> {topic}: {val_str}")
