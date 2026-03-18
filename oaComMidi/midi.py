# MIDI/midi_manager.py
# Modularized MIDI Orchestrator.
# Version 20260315.Modular.1

import threading
import time
import orjson
from loguru import logger

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from oaConfiguration.config_reader import Config
app_constants = Config.get_instance()
midi_logger = logger.bind(category="MIDI")

# --- EXTRACTED CORE MODULES ---
from .core.midi_port_controller import MIDIPortController
from .core.midi_hardware_lock import MIDIHardwareLock
from .core.midi_protocol_mapper import MIDIProtocolMapper

class MidiManager:
    """Manages bidirectional MIDI communication across ALL available ports."""

    def __init__(self, state_cache_manager=None, run_bridge=True):
        self.run_bridge, self.state_cache_manager = run_bridge, state_cache_manager
        self._running = False
        
        self.ports = MIDIPortController(midi_logger)
        self.lock_manager = MIDIHardwareLock()
        self.mapper = MIDIProtocolMapper()
        
        self._active_in_names, self._active_out_names = [], []
        self._monitor_callbacks = []

        from oaComsBroker.protocol_router import ProtocolRouter
        ProtocolRouter.get_instance().register_cache_observer(self._on_protocol_event)

    def add_monitor_callback(self, cb): self._monitor_callbacks.append(cb)
    def remove_monitor_callback(self, cb): (cb in self._monitor_callbacks) and self._monitor_callbacks.remove(cb)
    def _notify_monitor(self, d, m): [cb(d, m) for cb in self._monitor_callbacks]

    def get_port_info(self):
        return self.ports.get_port_info(self.run_bridge, self._active_in_names, self._active_out_names)

    def start(self):
        if self._running: return
        self._running = True
        if self.run_bridge:
            info = self.get_port_info()
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
        from oaComsBroker.protocol_router import ProtocolRouter
        router = ProtocolRouter.get_instance()
        while self._running:
            try:
                for msg in port.iter_pending():
                    topic, val = self.mapper.midi_to_topic(msg, port.name)
                    meta = {"midi_type": msg.type, "guid": f"{topic.split('/')[2]}/{getattr(msg, 'channel', 0)}", "msg_type": "SPLICE_ACTION", "origin_source": "MIDI"}

                    # Locking
                    if msg.type in ['control_change', 'pitchwheel', 'aftertouch', 'note_on']: self.lock_manager.lock(topic)
                    elif msg.type == 'note_off': self.lock_manager.unlock(topic)

                    router.ingest("MIDI", topic, val, meta)
                    if msg.type == 'control_change': self.lock_manager.delayed_unlock(topic)

                    self._notify_monitor("RX", msg)
                    if self.state_cache_manager:
                        pld = {"val": val}; hasattr(msg, "note") and pld.update({"note": msg.note})
                        self.state_cache_manager.handle_external_update(topic, pld, source="MIDI", metadata=meta)
            except Exception as e: midi_logger.error(f"❌ Listen Error on {port.name}: {e}")
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
                try: p.send(midi_msg); self._notify_monitor("TX", f"[{p.name}] {str(midi_msg)}")
                except Exception as e: midi_logger.error(f"❌ TX Error on {p.name}: {e}")
            
            from oaComsBroker.protocol_router import ProtocolRouter
            ProtocolRouter.get_instance().ingest("MIDI-TX", topic, rv, {"midi_raw": str(midi_msg), "msg_type": meta.get("msg_type"), "origin_source": meta.get("origin_source")})

    def _on_protocol_event(self, msg):
        if not self._running: return
        topic, val = str(msg.get("topic", "")), msg.get("val")
        if topic == "OPEN-AIR/System/Status/MIDI/ActiveInputs": self._active_in_names = val.get("val", val) if isinstance(val, (dict, list)) else []
        elif topic == "OPEN-AIR/System/Status/MIDI/ActiveOutputs": self._active_out_names = val.get("val", val) if isinstance(val, (dict, list)) else []
        elif not self.run_bridge and msg.get("logical_source") == "MIDI":
            tgt = val if (isinstance(val, dict) and "raw" in val) else msg.get("meta", {})
            if isinstance(tgt, dict) and "raw" in tgt: self._notify_monitor("RX", tgt)
