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
import re
from loguru import logger
from oaLogging.Methods.matrix_gate import matrix_log

# --- EXTRACTED CORE MODULES ---
from ..Core.midi_port_controller import MIDIPortController
from ..Core.midi_hardware_lock import MIDIHardwareLock
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

        # ⚡ MQTT WORKER: Direct connection to broker
        self.mqtt_worker = MidiMqttWorker(self) if self.enable_direct_mqtt else None

        if self.use_protocol_router:
            try:
                from oaComBroker.Core.protocol_router.manager import ProtocolRouter
                ProtocolRouter.get_instance().register_cache_observer(self._on_protocol_event)
            except Exception as e:
                logger.warning(f"🎹 [MIDI-MGR] Failed to register with ProtocolRouter: {e}")

    def add_monitor_callback(self, cb):
        with self._monitor_lock:
            if cb not in self._monitor_callbacks:
                self._monitor_callbacks.append(cb)

    def remove_monitor_callback(self, cb):
        with self._monitor_lock:
            if cb in self._monitor_callbacks:
                self._monitor_callbacks.remove(cb)

    def _notify_monitor(self, direction, msg):
        """Passes traffic details to local listeners (e.g. Dashboard)."""
        with self._monitor_lock:
            for cb in self._monitor_callbacks:
                try:
                    cb(direction, msg)
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
            info = self.get_port_info()
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

    def get_port_info(self):
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
                    msgs = list(port.iter_pending())
                else:
                    msg = port.receive(timeout=0.005)
                    msgs = [msg] if msg else []

                for msg in msgs:
                    # 1. Translate MIDI to System Topic
                    topic, val = self.mapper.midi_to_topic(msg, getattr(port, 'name', 'unknown'))
                    meta = {
                        "midi_type": msg.type, 
                        "guid": f"{topic.split('/')[2] if topic and '/' in topic else 'unknown'}/{getattr(msg, 'channel', 0)}", 
                        "midi_raw": str(msg),
                        "origin_source": "MIDI" # Required for tests
                    }

                    if topic:
                        # 2. Update Hardware Lock to prevent echo fighting
                        self.lock_manager.lock(topic)

                        # ⚡ LOCAL FIRST: Notify internal monitors (Dashboard) immediately
                        self._notify_monitor("RX", {
                            "val": getattr(msg, 'velocity', getattr(msg, 'value', 0)),
                            "velocity": getattr(msg, 'velocity', 0),
                            "channel": getattr(msg, 'channel', 0),
                            "note": getattr(msg, 'note', getattr(msg, 'control', 0)),
                            "type": msg.type,
                            "port": getattr(port, 'name', 'unknown'),
                            "raw": str(msg)
                        })

                        # 3. Inject into ProtocolRouter
                        if self.state_cache_manager:
                            self.state_cache_manager.handle_external_update(topic, val, source="MIDI", metadata=meta)
                        
                        # 4. Cleanup lock based on event type
                        if msg.type in ['note_on', 'note_off', 'control_change']:
                            if msg.type == 'note_on' and getattr(msg, 'velocity', 0) > 0:
                                pass # Keep locked while held? (Optional logic)
                            elif msg.type == 'note_off': 
                                self.lock_manager.unlock(topic)

                            if msg.type == 'control_change': 
                                self.lock_manager.delayed_unlock(topic)
                
                if _one_shot: break
                if not msgs:
                    time.sleep(0.001) # Yield to CPU
            except Exception as e:
                matrix_log("comms", "midi", "_midi_listen_loop", f"🛑 [MIDI-LISTEN] Error on {getattr(port, 'name', 'unknown')}: {e}", "ERROR")
                break

        # Don't close if it was passed in (tests)
        if isinstance(port_or_name, str):
            self.ports.close_input(port_or_name)

    # --- OUTBOUND: System -> MIDI Hardware ---

    def _on_protocol_event(self, msg):
        """
        Triggered when a protocol event is received (from ProtocolRouter/MQTT).
        Matches topics and determines if a MIDI message should be transmitted.
        """
        topic = msg.get("topic")
        val = msg.get("val")
        meta = msg.get("meta", msg.get("metadata", {}))
        source = msg.get("source", "UNKNOWN")
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
                real_val = val.get("val") if isinstance(val, dict) else val
                import re
                note_match = re.search(r"note(\d+)", topic)
                note = int(note_match.group(1)) if note_match else 0
                
                # Try to extract channel from topic as well
                channel_match = re.search(r"ch(\d+)", topic)
                channel = (int(channel_match.group(1)) - 1) if channel_match else 0

                m_type = "note_on" if real_val > 0 else "note_off"
                self._notify_monitor(direction, {
                    "val": real_val, 
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
            midi_msg = self.mapper.topic_to_midi(topic, val)
            if midi_msg:
                # Determine which port to send to (extracted from topic)
                # topic: OPEN-AIR/MIDI/<port_name>/...
                parts = topic.split('/')
                if len(parts) > 2:
                    target_port = parts[2]
                    self.publish(target_port, midi_msg)

    def publish(self, *args, **kwargs):
        """
        Sends a MIDI message. Supports multiple signatures:
        1. publish(port_name, midi_msg) - Direct hardware send
        2. publish(topic, val, meta) - Core router dispatch
        """
        if not self.run_bridge: return

        # Signature 1: Direct hardware send (port_name, mido_msg)
        if len(args) == 2 and hasattr(args[1], 'type'):
            port_name, midi_msg = args
            port = self.ports.open_output(port_name)
            if port:
                try:
                    port.send(midi_msg)
                except Exception as e:
                    matrix_log("comms", "midi", "publish", f"🛑 [MIDI-TX] Error sending to {port_name}: {e}", "ERROR")
            return

        # Signature 2: Core router dispatch (topic, val, meta)
        if len(args) >= 2:
            topic = args[0]
            val = args[1]
            meta = args[2] if len(args) > 2 else (kwargs.get('meta') or kwargs.get('metadata') or {})
            
            # Anti-feedback check
            if meta.get("origin_source") == "MIDI" or meta.get("source") == "MIDI":
                return

            midi_msg = self.mapper.topic_to_midi(topic, val)
            if midi_msg:
                # Hardware locks prevent us from moving a fader the user is currently touching
                if self.lock_manager.is_locked(topic):
                    matrix_log("comms", "midi", "publish", f"🎹 [MIDI-TX] Dropping update for {topic} (Hardware Locked)", "DEBUG")
                    return

                # Broadcast to ALL active outputs (simple Hub-and-Spoke model)
                for outport in self.ports.outports:
                    try:
                        outport.send(midi_msg)
                    except Exception as e:
                        logger.error(f"Failed to send MIDI to {getattr(outport, 'name', 'unknown')}: {e}")
