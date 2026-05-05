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

from oaLogging.Methods.matrix_gate import matrix_log
from oaOchestration.Managers.protocol_guard import protocol_guard

from .constants import app_constants


def dispatch_message(message, managers, topic_routing=None, is_active=True):
    """
    Executes transport-specific publication based on the routing strategy.
    """
    from oaComBroker.Core.protocol_router.manager import ProtocolRouter
    router = ProtocolRouter.get_instance()
    topic_routing_map = topic_routing or {}

    # Normalize Source Name for Matrix Lookup
    source_raw = str(message["source"]).upper()
    source = source_raw.replace("-TX", "") if "-TX" in source_raw else source_raw

    strategy = message.get("strategy", "")
    topic = message["topic"]
    value = message["value"]
    value_representation = str(value)[:100] + ("..." if len(str(value)) > 100 else "")

    # Helper to resolve topic override or prefixing
    def get_topic(dest):
        configuration_entry = topic_routing_map.get((source, dest))

        # ⚡ V3.1.15 OSC ADDRESS GUARD:
        # OSC typically uses its own address mapping. Do not force-prefix
        # unless a specific 'send' override is defined in the routing matrix.
        if dest == "OSC" and not (configuration_entry and configuration_entry.get("send")):
            return topic

        if configuration_entry and configuration_entry.get("send"):
            prefix = configuration_entry["send"].rstrip("/")

            # ⚡ V3.1.13 PREFIX GUARD:
            # Do not prefix topics that already belong to System or Monitor namespaces.
            if "/System/" in topic or "/Monitor/" in topic:
                return topic

            # ⚡ V3.1.14 RECURSION GUARD:
            # If the topic already starts with the intended prefix, return as-is.
            if topic.startswith(prefix + "/"):
                return topic

            # If it's a prefix, we strip ALL known protocol roots and existing 'OPEN-AIR/'
            # substrings to prevent recursive bloat (e.g., OPEN-AIR/OSC/OSC/MIDI).
            suffix = topic
            roots = ["OPEN-AIR/GUI", "OPEN-AIR/oaGui", "OPEN-AIR/MIDI", "OPEN-AIR/OSC",
                     "OPEN-AIR/NMOS", "OPEN-AIR/AES70", "OPEN-AIR/SMPTE2138", "OPEN-AIR/EMBER",
                     "OPEN-AIR"]

            for root in roots:
                # Aggressively remove redundant root prefixes
                while suffix.startswith(root):
                    suffix = suffix[len(root):].lstrip("/")

            return f"{prefix}/{suffix.lstrip('/')}"
        return topic

    # --- V3.0.0 SELF-FILTER / ECHO REMOVER ---
    # Acts as a gatekeeper for Output Commands.
    # It compares the incoming message's 'source' tag against the local module ID.
    message_source_id = message.get("meta", {}).get("source") or message.get("full_id")

    if message_source_id == app_constants.FULL_INSTANCE_ID:
        # ⚡ EXCEPTION: MQTT Broadcast (🚀), Cache (💾), and SNMP (Ⓢ) must proceed
        # for self-authored messages to ensure global state synchronization.
        if "🚀" not in strategy and "Ⓜ️" not in strategy and "💾" not in strategy and "Ⓢ" not in strategy:
            if app_constants.ROUTER_DISPATCH_LOGS:
                matrix_log("comms", "broker", "dispatch_message", f"🛡️ [ECHO] Dropping self-authored message for {topic}.", "TRACE")
            return

    # --- MQTT Dispatch ---
    if "🚀" in strategy or "Ⓜ️" in strategy:
        if is_active and router.routing_matrix.get(source, {}).get("MQTT", True):
            mqtt_manager = managers.get("mqtt")
            # ⚡ V3.1.26 DISPATCH UPDATE:
            # Allow MQTT dispatch if explicitly requested by strategy (🚀),
            # even if the source was MQTT (for broadcasts/activity logs).
            # We only block standard loopback if NO broadcast strategy is present.
            if mqtt_manager:
                _dispatch_mqtt(mqtt_manager, get_topic("MQTT"), message, value_representation)

    # --- OSC Dispatch ---
    if "🅾️" in strategy:
        if is_active and router.routing_matrix.get(source, {}).get("OSC", True):
            osc_manager = managers.get("osc")
            if osc_manager and message["source"] not in ["OSC", "OSC-TX"] and message.get("logical_source") not in ["OSC", "OSC-TX"]:
                # ⚡ V3.1.12 NAMESPACE EXCLUSION:
                is_gui = any(x in topic.upper() for x in ["/GUI/", "/OAGUI/"])
                is_system = "/SYSTEM/" in topic.upper()
                is_midi = "/MIDI/" in topic.upper()
                has_address = bool(message.get("meta", {}).get("osc_address"))

                if (is_gui or is_system or is_midi) and not has_address:
                    pass
                else:
                    _dispatch_osc(osc_manager, get_topic("OSC"), value, message, value_representation)

    # --- MIDI Dispatch ---
    if "🎹" in strategy:
        if is_active and router.routing_matrix.get(source, {}).get("MIDI", True):
            midi_manager = managers.get("midi")
            if midi_manager:
                # ⚡ V3.2.2 ROUTING UPDATE:
                # Allow MIDI dispatch if the message is an intent (SPLICE_ACTION).
                # This ensures that GUI-generated MIDI events (which carry the MIDI topic prefix)
                # are correctly routed to the hardware managers in the CORE partition.
                # We only block messages that are direct feedback (LINK_FEEDBACK)
                # from the MIDI hardware itself to prevent infinite loops.
                is_midi_hw = (message["source"] == "MIDI")
                is_feedback = (message.get("message_type") == "LINK_FEEDBACK")

                if not (is_midi_hw or is_feedback):
                    _dispatch_midi(midi_manager, get_topic("MIDI"), value, message, value_representation)

    # --- SNMP Dispatch ---
    if "Ⓢ" in strategy:
        if is_active and router.routing_matrix.get(source, {}).get("SNMP", True):
            snmp_manager = managers.get("snmp")
            if snmp_manager and message["source"] not in ["SNMP", "SNMP-TX"] and message.get("logical_source") not in ["SNMP", "SNMP-TX"]:
                _dispatch_snmp(snmp_manager, get_topic("SNMP"), value, value_representation)

    # --- NMOS Dispatch ---
    if "N" in strategy or "NMOS" in strategy:
        if is_active and router.routing_matrix.get(source, {}).get("NMOS", True):
            nmos_manager = managers.get("nmos")
            if nmos_manager and message["source"] != "NMOS" and message.get("logical_source") != "NMOS":
                _dispatch_nmos(nmos_manager, get_topic("NMOS"), value, message, value_representation)

    # --- SMPTE 2138 Dispatch ---
    if "🔗" in strategy or "🚀" in strategy:
        if is_active and router.routing_matrix.get(source, {}).get("SMPTE2138", True):
            smpte_manager = managers.get("smpte2138")
            if smpte_manager and message["source"] != "SMPTE2138" and message.get("logical_source") != "SMPTE2138":
                _dispatch_smpte2138(smpte_manager, get_topic("SMPTE2138"), value, message, value_representation)

@protocol_guard("MQTT")
def _dispatch_mqtt(mqtt_manager, topic, message, value_representation):
    payload = {
        "value": message["value"], "source": message.get("logical_source", message["source"]),
        "timestamp": message["timestamp"], "GUID": message["guid"], "partition": message["partition"]
    }
    if isinstance(message.get("meta"), dict): payload.update(message["meta"])

    # ⚡ V3.1.12 ACKNOWLEDGEMENT REMOVAL:
    # Automatic /Tx/ namespace prefixing has been permanently removed to
    # prevent topic tree clutter. Standard topic paths are preserved.
    tx_topic = topic

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
        matrix_log("comms", "broker", "_dispatch_mqtt", f"📡📤📤 [OUTBOUND] MQTT >> {tx_topic} (Retain={retain}): {value_representation}", "DEBUG")

@protocol_guard("OSC")
def _dispatch_osc(osc_manager, topic, value, message, value_representation):
    osc_address = message["meta"].get("osc_address", "/" + topic.replace("OPEN-AIR/", ""))

    # ⚡ RESILIENCE: Handle complex GUI-sourced payloads
    if isinstance(value, dict) and "value" in value:
        payload = value["value"]
    else:
        payload = value

    osc_manager.send(osc_address, payload)
    if app_constants.ROUTER_DISPATCH_LOGS:
        matrix_log("comms", "broker", "_dispatch_osc", f"📡📤📤 [OUTBOUND] OSC >> {osc_address}: {value_representation}", "DEBUG")

@protocol_guard("MIDI")
def _dispatch_midi(midi_manager, topic, value, message, value_representation):
    midi_manager.publish(topic, value, message["meta"])
    if app_constants.ROUTER_DISPATCH_LOGS:
        matrix_log("comms", "broker", "_dispatch_midi", f"📡📤📤 [MIDI] >> {topic}: {value_representation}", "DEBUG")

@protocol_guard("SNMP")
def _dispatch_snmp(snmp_manager, topic, value, value_representation):
    snmp_manager.publish(topic, value)
    if app_constants.ROUTER_DISPATCH_LOGS:
        matrix_log("comms", "broker", "_dispatch_snmp", f"📡📤📤 [SNMP] >> {topic}: {value_representation}", "DEBUG")

@protocol_guard("NMOS")
def _dispatch_nmos(nmos_manager, topic, value, message, value_representation):
    """Routes normalized internal actions to the NMOS IS-07 bridge."""
    nmos_manager.handle_router_event(topic, value, message.get("meta", {}))
    if app_constants.ROUTER_DISPATCH_LOGS:
        matrix_log("comms", "broker", "_dispatch_nmos", f"📡📤📤 [NMOS] >> {topic}: {value_representation}", "DEBUG")

@protocol_guard("SMPTE2138")
def _dispatch_smpte2138(smpte_manager, topic, value, message, value_representation):
    """Routes normalized internal actions to the SMPTE 2138 bridge."""
    # The manager's ingest method handles OID mapping and Protobuf encoding.
    smpte_manager.handle_router_event(topic, value, message.get("meta", {}))
    if app_constants.ROUTER_DISPATCH_LOGS:
        matrix_log("comms", "broker", "_dispatch_smpte2138", f"📡📤📤 [SMPTE2138] >> {topic}: {value_representation}", "DEBUG")
