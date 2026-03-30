# oaComMidi/Managers/midi_manager.py
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
# Version 20260328.1405.1

import threading
import time
import orjson
from loguru import logger

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()
from oaLogging.Core.logger import MIDI_LOGGER as midi_logger

# --- EXTRACTED CORE MODULES ---
from ..Core.midi_port_controller import MIDIPortController
from ..Core.midi_hardware_lock import MIDIHardwareLock
from ..Core.midi_protocol_mapper import MIDIProtocolMapper

class MidiManager:
    """Manages bidirectional MIDI communication across ALL available ports."""

    def __init__(self, state_cache_manager=None, run_bridge=True):
        self.run_bridge, self.state_cache_manager = run_bridge, state_cache_manager
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
            
        if LOCAL_DEBUG:
            logger.trace(f"🎹 [MIDI-MGR] Notifying {len(callbacks)} monitors of {direction} activity.")

        for cb in callbacks:
            try:
                cb(direction, msg)
            except Exception as e:
                if LOCAL_DEBUG:
                    logger.error(f"❌ [MIDI-MGR] Monitor callback failed: {e}")

    def get_port_info(self):
        return self.ports.get_port_info(self.run_bridge, self._active_in_names, self._active_out_names)

    def start(self):
        if self._running: return
        self._running = True
        if self.run_bridge:
            info = self.get_port_info()
            if LOCAL_DEBUG:
                midi_logger.info(f"🎹 [MIDI-MGR] Starting bridge. Found {len(info.get('inputs', []))} inputs, {len(info.get('outputs', []))} outputs.")
            self.ports.open_all(info, self._midi_listen_loop)
            self._broadcast_status()

    def stop(self):
        self._running = False
        self.ports.close_all()

    def _broadcast_status(self):
        if self.state_cache_manager and self.run_bridge:
            for p, n in [("Inputs", [p.name for p in self.ports.inports]), ("Outputs", [p.name for p in self.ports.outports])]:
                self.state_cache_manager.handle_external_update(f"OPEN-AIR/System/Status/MIDI/Active{p}", n, source="MIDI")

    def _midi_listen_loop(self, port):
        if LOCAL_DEBUG:
            midi_logger.debug(f"▶️ [MIDI-LISTEN] Started listening on port: {port.name}")
        
        last_heartbeat = 0
        while self._running:
            try:
                # Periodic heartbeat to prove loop is alive (every 30s)
                if time.time() - last_heartbeat > 30:
                    if LOCAL_DEBUG:
                        midi_logger.debug(f"💓 [MIDI-LISTEN] Loop active for {port.name}")
                    last_heartbeat = time.time()

                for msg in port.iter_pending():
                    if LOCAL_DEBUG:
                        midi_logger.trace(f"🎹 [MIDI-LISTEN] Incoming: {msg} on {port.name}")
                    
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
                    # handle_external_update updates cache, notifies router, and triggers MQTT publish.
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
                        
            except Exception as e:
                midi_logger.error(f"Listen Error on {port.name}: {e}")
            
            time.sleep(0.001)

    def publish(self, topic, val, meta=None):
        if not self._running or not self.run_bridge: return
        meta = meta or {}
        if self.lock_manager.is_locked(topic) or meta.get("origin_source") == "MIDI": return
        if meta.get("msg_type") == "LINK_FEEDBACK" and not meta.get("is_settled"): return

        rv = val.get("val") if (isinstance(val, dict) and "val" in val) else val
        midi_msg = self.mapper.topic_to_midi(topic, rv)
        if midi_msg:
            for p in self.ports.outports:
                try:
                    p.send(midi_msg)
                    self._notify_monitor("TX", f"[{p.name}] {str(midi_msg)}")
                except Exception as e:
                    midi_logger.error(f"TX Error on {p.name}: {e}")
            
            from oaComBroker.Core.protocol_router.manager import ProtocolRouter
            ProtocolRouter.get_instance().ingest("MIDI-TX", topic, rv, {"midi_raw": str(midi_msg), "msg_type": meta.get("msg_type"), "origin_source": meta.get("origin_source")})

    def _on_protocol_event(self, msg):
        topic, val = str(msg.get("topic", "")), msg.get("val")
        
        # 1. Hardware Status Updates
        if topic == "OPEN-AIR/System/Status/MIDI/ActiveInputs": 
            self._active_in_names = val.get("val", val) if isinstance(val, (dict, list)) else []
        elif topic == "OPEN-AIR/System/Status/MIDI/ActiveOutputs": 
            self._active_out_names = val.get("val", val) if isinstance(val, (dict, list)) else []
        
        # 2. Activity Monitoring
        # We listen for any MIDI topic traffic to update the visualizers.
        is_midi_topic = "/MIDI/" in topic
        is_midi_source = msg.get("logical_source") in ["MIDI", "MIDI-TX"]
        
        if is_midi_topic or is_midi_source:
            if LOCAL_DEBUG:
                logger.trace(f"🎹 [MIDI-MGR] MIDI event detected on {topic} (Source: {msg.get('logical_source')})")
            
            # Determine direction
            direction = "TX" if msg.get("logical_source") == "MIDI-TX" else "RX"
            
            # We expect enriched payload (dict) from CORE
            if isinstance(val, dict) and "raw" in val:
                self._notify_monitor(direction, val)
            elif isinstance(val, (int, float, dict)) and is_midi_topic:
                # Fallback for simple values or manifests on MIDI topics
                real_val = val.get("val") if isinstance(val, dict) else val
                self._notify_monitor(direction, {"val": real_val, "topic": topic, "type": "note_on" if real_val > 0 else "note_off"})
