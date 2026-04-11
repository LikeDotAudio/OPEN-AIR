# oaComProtocols.oaComMidi/Managers/midi_manager.py
#
# Main orchestrator for bidirectional MIDI communication.
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

import threading
import time
import orjson
import re
from loguru import logger

# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config
app_constants = Config.get_instance()
from oaLogging.Core.logger import MIDI_LOGGER as midi_logger
from oaLogging.Methods.matrix_gate import matrix_log

# --- EXTRACTED CORE MODULES ---
from ..Core.midi_port_controller import MIDIPortController
from ..Core.midi_hardware_lock import MIDIHardwareLock
from ..Core.midi_protocol_mapper import MIDIProtocolMapper

class MidiManager:
    """Manages bidirectional MIDI communication across ALL available ports."""

    def __init__(self, state_cache_manager=None, run_bridge=True, auto_start=True):
        self.run_bridge, self.state_cache_manager = run_bridge, state_cache_manager
        self.auto_start = auto_start
        self._running = False
        
        # ⚡ THREAD SAFETY: Protect shared mutable state
        self._monitor_lock = threading.Lock()
        
        self.ports = MIDIPortController(midi_logger)
        self.lock_manager = MIDIHardwareLock()
        self.mapper = MIDIProtocolMapper()
        
        self._active_in_names, self._active_out_names = [], []
        self._monitor_callbacks = []

        from oaComBroker.Core.protocol_router.manager import ProtocolRouter
        ProtocolRouter.get_instance().register_cache_observer(self._on_protocol_event)

    def add_monitor_callback(self, cb):
        with self._monitor_lock:
            if cb not in self._monitor_callbacks:
                self._monitor_callbacks.append(cb)

    def remove_monitor_callback(self, cb):
        with self._monitor_lock:
            if cb in self._monitor_callbacks:
                self._monitor_callbacks.remove(cb)

    def _notify_monitor(self, direction, msg):
        # Take a snapshot to avoid holding lock during callback execution
        with self._monitor_lock:
            callbacks = list(self._monitor_callbacks)
            
        matrix_log("comms", "midi", "_notify_monitor", 
                   f"🎹 [MIDI-MGR] Notifying {len(callbacks)} monitors of {direction} activity.", "TRACE")

        for cb in callbacks:
            try:
                cb(direction, msg)
            except Exception as e:
                matrix_log("comms", "midi", "_notify_monitor", 
                           f"❌ [MIDI-MGR] Monitor callback failed: {e}", "ERROR")

    def get_port_info(self):
        return self.ports.get_port_info(self.run_bridge, self._active_in_names, self._active_out_names)

    def start(self):
        if self._running: return
        self._running = True
        
        mode = "BRIDGE" if self.run_bridge else "OBSERVER"
        matrix_log("comms", "midi", "start", f"🎹 [MIDI-MGR] Starting manager in {mode} mode.", "INFO")
        
        if self.run_bridge:
            info = self.get_port_info()
            matrix_log("comms", "midi", "start", 
                       f"🎹 [MIDI-MGR] Found {len(info.get('inputs', []))} inputs, {len(info.get('outputs', []))} outputs.", "INFO")
            
            if self.auto_start:
                self.ports.open_all(info, self._midi_listen_loop)
            
            self._broadcast_status()
        else:
            # In Observer mode, we rely on Core to broadcast status over MQTT.
            # We already registered as a cache observer in __init__.
            matrix_log("comms", "midi", "start", "🎹 [MIDI-MGR] Observer mode active. Waiting for Core status broadcast...", "DEBUG")

    def stop(self):
        self._running = False
        self.ports.close_all()

    def _broadcast_status(self):
        if self.state_cache_manager and self.run_bridge:
            for p, n in [("Inputs", [p.name for p in self.ports.inports]), ("Outputs", [p.name for p in self.ports.outports])]:
                self.state_cache_manager.handle_external_update(f"OPEN-AIR/System/Status/MIDI/Active{p}", n, source="MIDI")

    def _midi_listen_loop(self, port, _one_shot=False):
        matrix_log("comms", "midi", "_midi_listen_loop", 
                   f"▶️ [MIDI-LISTEN] Started listening on port: {port.name}", "DEBUG")
        
        last_heartbeat = 0
        while self._running:
            if not self._running: break
            try:
                # Periodic heartbeat to prove loop is alive (every 30s)
                if time.time() - last_heartbeat > 30:
                    matrix_log("comms", "midi", "_midi_listen_loop", 
                               f"💓 [MIDI-LISTEN] Loop active for {port.name}", "DEBUG")
                    last_heartbeat = time.time()

                for msg in port.iter_pending():
                    try:
                        matrix_log("comms", "midi", "_midi_listen_loop", 
                                   f"🎹 [MIDI-LISTEN] Incoming: {msg} on {port.name}", "TRACE")
                        
                        # ⚡ LOCAL FIRST: Notify internal monitors (Dashboard) immediately
                        self._notify_monitor("RX", msg)
                        
                        topic, val = self.mapper.midi_to_topic(msg, port.name)
                        meta = {
                            "midi_type": msg.type, 
                            "guid": f"{topic.split('/')[2]}/{getattr(msg, 'channel', 0)}", 
                            "msg_type": "SPLICE_ACTION", 
                            "origin_source": "MIDI"
                        }

                        # Hardware Locking
                        if msg.type in ['control_change', 'pitchwheel', 'aftertouch', 'note_on']: 
                            self.lock_manager.lock(topic)
                        elif msg.type == 'note_off': 
                            self.lock_manager.unlock(topic)

                        if msg.type == 'control_change': 
                            self.lock_manager.delayed_unlock(topic)

                        # ⚡ CENTRAL ORCHESTRATION: 
                        if self.state_cache_manager:
                            pld = {
                                "val": val,
                                "channel": getattr(msg, 'channel', 0),
                                "note": getattr(msg, 'note', 0),
                                "velocity": getattr(msg, 'velocity', 0),
                                "type": msg.type,
                                "raw": str(msg)
                            }
                            self.state_cache_manager.handle_external_update(topic, pld, source="MIDI", metadata=meta)
                        else:
                            # Fallback if no state manager (Standalone mode)
                            from oaComBroker.Core.protocol_router.manager import ProtocolRouter
                            ProtocolRouter.get_instance().ingest("MIDI", topic, val, meta)
                    except Exception as loop_e:
                         midi_logger.error(f"FATAL: Unhandled exception in MIDI processing loop for {port.name}: {loop_e}")

            except Exception as e:
                midi_logger.error(f"Listen Error on {port.name}: {e}")
            
            if _one_shot: break
            time.sleep(0.001)

    def publish(self, topic, val, meta=None):
        if not self._running or not self.run_bridge: return
        meta = meta or {}
        
        # ⚡ V3.2.0 FILTERING: Prevent reflection of non-MIDI sources back into the Hub
        origin_source = meta.get("origin_source", "UNKNOWN")
        if origin_source == "MIDI": return

        # Discard the message (Echo Removal) if the origin is MIDI
        if self.lock_manager.is_locked(topic): return
        if meta.get("msg_type") == "LINK_FEEDBACK" and not meta.get("is_settled"): return

        rv = val.get("val") if (isinstance(val, dict) and "val" in val) else val
        midi_msg = self.mapper.topic_to_midi(topic, rv)
        
        if midi_msg:
            target_port = meta.get("target_port")
            for p in self.ports.outports:
                try:
                    # If target_port is specified, only send to that port.
                    # Otherwise, broadcast to all.
                    if target_port and p.name != target_port:
                        continue
                        
                    p.send(midi_msg)
                    self._notify_monitor("TX", f"[{p.name}] {str(midi_msg)}")
                except Exception as e:
                    midi_logger.error(f"TX Error on {p.name}: {e}")
            
            # Re-ingest as MIDI-TX to sync other monitors
            from oaComBroker.Core.protocol_router.manager import ProtocolRouter
            ProtocolRouter.get_instance().ingest("MIDI-TX", topic, rv, {
                "midi_raw": str(midi_msg), 
                "msg_type": meta.get("msg_type"), 
                "origin_source": meta.get("origin_source"),
                "target_port": target_port
            })

    def _on_protocol_event(self, msg):
        topic, val = str(msg.get("topic", "")), msg.get("val")
        meta = msg.get("meta", {})
        source = msg.get("source", "UNKNOWN").upper()
        
        # 1. Hardware Status Updates
        if topic == "OPEN-AIR/System/Status/MIDI/ActiveInputs": 
            self._active_in_names = val if isinstance(val, list) else (val.get("val", []) if isinstance(val, dict) else [])
        elif topic == "OPEN-AIR/System/Status/MIDI/ActiveOutputs": 
            self._active_out_names = val if isinstance(val, list) else (val.get("val", []) if isinstance(val, dict) else [])
        
        # 2. Activity Monitoring
        # ⚡ V3.1.8 MONITOR REFLECTION:
        # We listen for MIDI topic traffic to update visualizers.
        # We allow self-authored reflections (Source: MQTT, same GUID) to proceed 
        # to the monitor, but we do NOT send them to hardware (handled in publish).
        is_midi_topic = "/MIDI/" in topic
        is_midi_source = msg.get("logical_source") in ["MIDI", "MIDI-TX"]
        
        if is_midi_topic or is_midi_source:
            # Determine direction
            is_tx = msg.get("logical_source") == "MIDI-TX" or meta.get("midi_raw") is not None
            direction = "TX" if is_tx else "RX"
            
            # Prefer enriched metadata from MQTT if available
            if isinstance(meta, dict) and "raw" in meta:
                self._notify_monitor(direction, meta)
            elif isinstance(val, dict) and "raw" in val:
                # ⚡ V3.2.1 ENHANCEMENT: If payload is a full MIDI mirror, pass it as-is
                self._notify_monitor(direction, val)
            elif is_midi_topic:
                # Fallback for primitive MQTT value updates
                real_val = val.get("val") if isinstance(val, dict) else val
                note_match = re.search(r"note(\d+)", topic)
                note = int(note_match.group(1)) if note_match else 0
                
                # Try to extract channel from topic as well
                channel_match = re.search(r"ch(\d+)", topic)
                channel = int(channel_match.group(1)) if channel_match else 0

                self._notify_monitor(direction, {
                    "val": real_val, 
                    "topic": topic, 
                    "note": note,
                    "channel": channel,
                    "velocity": real_val if real_val <= 127 else 127,
                    "type": "note_on" if real_val > 0 else "note_off",
                    "raw": f"note={note} channel={channel} velocity={real_val}"
                })
