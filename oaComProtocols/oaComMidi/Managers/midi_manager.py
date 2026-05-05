# oaComProtocols.oaComMidi/Managers/midi_manager.py
#
# Main orchestrator for bidirectional MIDI communication.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for critical audio/video systems.
# Version: 20260412.0130.1

import threading
import time

from loguru import logger

from oaLogging.Methods.matrix_gate import matrix_log

from ..Core.midi_hardware_lock import MIDIHardwareLock
from ..Core.midi_mqtt_transport import MidiMqttTransport

# --- EXTRACTED CORE MODULES ---
from ..Core.midi_port_controller import MIDIPortController
from ..Core.midi_protocol_mapper import MIDIProtocolMapper
from ..Workers.midi_mqtt_worker import MidiMqttWorker


class MidiManager:
    """Manages bidirectional MIDI communication across ALL available ports."""

    def __init__(self, state_cache_manager=None, run_bridge=True, auto_start=True, use_protocol_router=True, enable_direct_mqtt=True):
        self.run_bridge, self.state_cache_manager = run_bridge, state_cache_manager
        self.auto_start = auto_start
        self.use_protocol_router = use_protocol_router
        self.enable_direct_mqtt = enable_direct_mqtt
        self._running = False

        # ⚡ THREAD SAFETY: Protect shared mutable state
        self._monitor_lock = threading.Lock()

        # Internal components
        self.ports = MIDIPortController(logger)
        self.lock_manager = MIDIHardwareLock()
        self.mapper = MIDIProtocolMapper()

        self._active_in_names, self._active_out_names = [], []
        self._monitor_callbacks = []

        # ⚡ CORE TRANSPORT: Native MIDI MQTT Transport
        self.mqtt_transport = MidiMqttTransport() if self.enable_direct_mqtt else None

        # ⚡ MQTT WORKER: Legacy wrapper for background operations if needed,
        # but we'll prioritize the core transport.
        self.mqtt_worker = MidiMqttWorker(self, transport=self.mqtt_transport) if self.enable_direct_mqtt else None

        if self.use_protocol_router:
            pass # ProtocolRouter dependency removed

    def add_monitor_callback(self, cb):
        with self._monitor_lock:
            if cb not in self._monitor_callbacks:
                self._monitor_callbacks.append(cb)

    def remove_monitor_callback(self, cb):
        with self._monitor_lock:
            if cb in self._monitor_callbacks:
                self._monitor_callbacks.remove(cb)

    def _notify_monitor(self, direction, message):
        """Passes traffic details to local listeners (e.g. Dashboard)."""
        with self._monitor_lock:
            for cb in self._monitor_callbacks:
                try:
                    cb(direction, message)
                except Exception as e:
                    logger.error(f"🎹 [MIDI-MGR] Monitor callback error: {e}")

    def start(self):
        if self._running: return
        self._running = True

        mode = "BRIDGE" if self.run_bridge else "OBSERVER"
        matrix_log("comms", "midi", "start", f"🎹 [MIDI-MGR] Starting manager in {mode} mode.", "INFO")

        if self.mqtt_worker:
            self.mqtt_worker.start()

        if self.run_bridge:
            info = self.queryPortStatus()
            matrix_log("comms", "midi", "start",
                       f"🎹 [MIDI-MGR] Found {len(info.get('inputs', []))} inputs, {len(info.get('outputs', []))} outputs.", "INFO")

            # Start listeners for each input port
            for port_name in info.get("inputs", []):
                t = threading.Thread(target=self._midi_listen_loop, args=(port_name,), daemon=True)
                t.start()

            # Start status broadcast thread
            threading.Thread(target=self._telemetry_loop, daemon=True).start()
        else:
            matrix_log("comms", "midi", "start", "🎹 [MIDI-MGR] Observer mode active. Waiting for Core status broadcast.", "DEBUG")

    def stop(self):
        self._running = False
        self.ports.close_all()
        if self.mqtt_worker:
            self.mqtt_worker.stop()

    def status(self):
        return {
            "running": self._running,
            "bridge": self.run_bridge,
            "inputs": self._active_in_names,
            "outputs": self._active_out_names
        }

    def queryPortStatus(self):
        # Support old signature from MIDIPortController if needed
        # (Though we added get_available_ports to it recently)
        return self.ports.get_available_ports()

    def _telemetry_loop(self):
        """Periodically broadcasts active ports to the system."""
        while self._running:
            self._broadcast_status()
            time.sleep(10) # Every 10 seconds

    def _broadcast_status(self):
        """Forces a status update to the state cache."""
        if not self.state_cache_manager: return

        info = self.ports.get_available_ports()

        for p, n in [("Inputs", info.get("inputs", [])), ("Outputs", info.get("outputs", []))]:
            self.state_cache_manager.handle_external_update(f"OPEN-AIR/System/Status/MIDI/Active{p}", n, source="MIDI")

    # --- INBOUND: MIDI Hardware -> System ---

    def _midi_listen_loop(self, port_or_name, _one_shot=False):
        """High-priority loop for reading from a physical MIDI port."""
        if isinstance(port_or_name, str):
            port = self.ports.open_input(port_or_name)
        else:
            port = port_or_name # Support passing mock port for tests

        if not port: return

        matrix_log("comms", "midi", "_midi_listen_loop", f"▶️ [MIDI-LISTEN] Started listening on port: {getattr(port, 'name', 'unknown')}", "DEBUG")

        while self._running:
            try:
                # Support tests that use iter_pending
                if hasattr(port, 'iter_pending'):
                    messages = list(port.iter_pending())
                else:
                    message = port.receive(timeout=0.005)
                    messages = [message] if message else []

                for message in messages:
                    # 1. Translate MIDI to System Topic
                    topic, value = self.mapper.midi_to_topic(message, getattr(port, 'name', 'unknown'))
                    meta = {
                        "midi_type": message.type,
                        "guid": f"{topic.split('/')[2] if topic and '/' in topic else 'unknown'}/{getattr(message, 'channel', 0)}",
                        "midi_raw": str(message),
                        "origin_source": "MIDI" # Required for tests
                    }

                    if topic:
                        # 2. Update Hardware Lock to prevent echo fighting
                        self.lock_manager.lock(topic)

                        # ⚡ LOCAL FIRST: Notify internal monitors (Dashboard) immediately
                        self._notify_monitor("RX", {
                            "value": getattr(message, 'velocity', getattr(message, 'value', 0)),
                            "velocity": getattr(message, 'velocity', 0),
                            "channel": getattr(message, 'channel', 0),
                            "note": getattr(message, 'note', getattr(message, 'control', 0)),
                            "type": message.type,
                            "port": getattr(port, 'name', 'unknown'),
                            "raw": str(message)
                        })

                        # 3. Inject into ProtocolRouter
                        if self.state_cache_manager:
                            self.state_cache_manager.handle_external_update(topic, value, source="MIDI", metadata=meta)

                        # ⚡ DIRECT MQTT: Broadcast directly to broker if active (Standalone)
                        if self.mqtt_worker:
                            self.mqtt_worker.publish(topic, value, meta)

                        # 4. Cleanup lock based on event type
                        if message.type in ['note_on', 'note_off', 'control_change']:
                            if message.type == 'note_on' and getattr(message, 'velocity', 0) > 0:
                                pass # Keep locked while held? (Optional logic)
                            elif message.type == 'note_off':
                                self.lock_manager.unlock(topic)

                            if message.type == 'control_change':
                                self.lock_manager.delayed_unlock(topic)

                if _one_shot: break
                if not messages:
                    time.sleep(0.001) # Yield to CPU
            except Exception as e:
                matrix_log("comms", "midi", "_midi_listen_loop", f"🛑 [MIDI-LISTEN] Error on {getattr(port, 'name', 'unknown')}: {e}", "ERROR")
                break

        # Don't close if it was passed in (tests)
        if isinstance(port_or_name, str):
            self.ports.close_input(port_or_name)

    # --- OUTBOUND: System -> MIDI Hardware ---

    def _on_protocol_event(self, message):
        """
        Triggered when a protocol event is received (from ProtocolRouter/MQTT).
        Matches topics and determines if a MIDI message should be transmitted.
        """
        topic = message.get("topic")
        value = message.get("value")
        meta = message.get("meta", message.get("metadata", {}))
        source = message.get("source", "UNKNOWN")
        direction = "TX"

        # 1. Loop Prevention: Ignore if WE were the source
        if source == "MIDI" or source == "MIDI-TX" or meta.get("origin_source") == "MIDI":
            return

        # 2. Check if topic belongs to MIDI namespace
        is_midi_topic = topic.startswith("OPEN-AIR/MIDI/")

        # 3. Handle specific MIDI topics (Reflected from MQTT or link feedback)
        if is_midi_topic:
            # Reconstruct the monitor notification for GUI visualization
            try:
                real_val = value.get("value") if isinstance(value, dict) else value
                import re
                note_match = re.search(r"note(\d+)", topic)
                note = int(note_match.group(1)) if note_match else 0

                # Try to extract channel from topic as well
                channel_match = re.search(r"ch(\d+)", topic)
                channel = (int(channel_match.group(1)) - 1) if channel_match else 0

                m_type = "note_on" if real_val > 0 else "note_off"
                self._notify_monitor(direction, {
                    "value": real_val,
                    "topic": topic,
                    "note": note,
                    "channel": channel,
                    "velocity": real_val if isinstance(real_val, (int, float)) and real_val <= 127 else 127,
                    "type": m_type,
                    "raw": f"{m_type} note={note} channel={channel} velocity={real_val}"
                })
            except Exception: pass

            if not self.run_bridge: return # Observers only monitor, they don't transmit

            # 4. Translate back to MIDI and transmit
            midi_message = self.mapper.topic_to_midi(topic, value)
            if midi_message:
                # Determine which port to send to (extracted from topic)
                # topic: OPEN-AIR/MIDI/<port_name>/...
                parts = topic.split('/')
                if len(parts) > 2:
                    target_port = parts[2]
                    self.publish(target_port, midi_message)

    def publish(self, *args, **kwargs):
        """
        Sends a MIDI message. Supports multiple signatures:
        1. publish(port_name, midi_message) - Direct hardware send
        2. publish(topic, value, meta) - Core router dispatch
        """
        if not self.run_bridge: return

        # Signature 1: Direct hardware send (port_name, mido_message)
        if len(args) == 2 and hasattr(args[1], 'type'):
            port_name, midi_message = args
            port = self.ports.open_output(port_name)
            if port:
                try:
                    port.send(midi_message)
                except Exception as e:
                    matrix_log("comms", "midi", "publish", f"🛑 [MIDI-TX] Error sending to {port_name}: {e}", "ERROR")
            return

        # Signature 2: Core router dispatch (topic, value, meta)
        if len(args) >= 2:
            topic = args[0]
            value = args[1]
            meta = args[2] if len(args) > 2 else (kwargs.get('meta') or kwargs.get('metadata') or {})

            # Anti-feedback check
            if meta.get("origin_source") == "MIDI" or meta.get("source") == "MIDI":
                return

            midi_message = self.mapper.topic_to_midi(topic, value)
            if midi_message:
                # Hardware locks prevent us from moving a fader the user is currently touching
                if self.lock_manager.is_locked(topic):
                    matrix_log("comms", "midi", "publish", f"🎹 [MIDI-TX] Dropping update for {topic} (Hardware Locked)", "DEBUG")
                    return

                # Broadcast to ALL active outputs (simple Hub-and-Spoke model)
                for outport in self.ports.outports:
                    try:
                        outport.send(midi_message)
                    except Exception as e:
                        logger.error(f"Failed to send MIDI to {getattr(outport, 'name', 'unknown')}: {e}")

    def publish_batch(self, messages):
        """
        Processes a batch of MIDI messages.
        Args:
            messages: List of tuples matching publish() arguments.
        """
        if not self.run_bridge: return
        # Direct iteration is fine here as open_output and send are optimized.
        for msg in messages:
            if isinstance(msg, (list, tuple)):
                self.publish(*msg)
            else:
                self.publish(msg)
