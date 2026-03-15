# workers/Command_Router/MIDI/midi_manager.py
#
# Dedicated orchestrator for MIDI traffic.
# Handles bidirectional mapping for ALL detected ports.
#
# Author: Gemini Agent
# Version 20260308.Verbosed.2

import threading
import time
import orjson
import os
import re
from pathlib import Path

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from loguru import logger
from managers.configini.config_reader import Config

try:
    import mido
except ImportError:
    mido = None

app_constants = Config.get_instance()
midi_logger = logger.bind(category="MIDI")

class MidiManager:
    """
    Manages bidirectional MIDI communication across ALL available ports.
    Logic-heavy, UI-light architecture.
    """

    def __init__(self, state_cache_manager=None, run_bridge=True):
        self.run_bridge = run_bridge
        if LOCAL_DEBUG:
            midi_logger.info(f"🎹🎼💻 [MIDI] Initializing Engine "
                             f"(Bridge={run_bridge})...")

        self.state_cache_manager = state_cache_manager
        self._running = False
        
        # ⚡ HARDWARE INTERACTION LOCK: 
        # Tracks which parameters (topics) are currently being moved by a human finger.
        self._hardware_locked_params = set()
        self._lock_mutex = threading.Lock()

        # Workers: Lists for Multi-Port support
        self.inports = []
        self.outports = []
        self._listen_threads = []
        
        # Performance Caches
        self._dev_id_cache = {}

        # Internal Status Cache for UI
        self._active_in_names = []
        self._active_out_names = []

        # Monitor callbacks for GUI
        self._monitor_callbacks = []

        # Protocol Router Sync Logic: Listen for remote/local activity
        from workers.Command_Router.protocol_router import ProtocolRouter
        ProtocolRouter.get_instance().add_observer(self._on_protocol_event)

    def add_monitor_callback(self, callback):
        self._monitor_callbacks.append(callback)

    def remove_monitor_callback(self, callback):
        if callback in self._monitor_callbacks:
            self._monitor_callbacks.remove(callback)

    def _notify_monitor(self, direction, msg_str):
        for cb in self._monitor_callbacks:
            try: cb(direction, msg_str)
            except: pass

    def get_port_info(self):
        """Logic-only port scan. Returns a dictionary for the UI to consume."""
        if mido is None:
            return {"error": "mido library missing"}
            
        try:
            inputs = mido.get_input_names()
            outputs = mido.get_output_names()
            
            # Use local ports if we are the bridge, otherwise use synced lists
            active_in = [p.name for p in self.inports] if self.run_bridge \
                        else self._active_in_names
            active_out = [p.name for p in self.outports] if self.run_bridge \
                         else self._active_out_names

            return {
                "inputs": inputs,
                "outputs": outputs,
                "active_in": active_in,
                "active_out": active_out,
                "error": None
            }
        except Exception as e:
            midi_logger.error(f"❌🚫🛑 [MIDI] Scan Failed: {e}")
            return {"error": str(e)}

    def start(self):
        """Initializes and starts MIDI workers for all detected ports."""
        if self._running: 
            midi_logger.warning("🎹🎼⚠️ [MIDI] Engine already running. Skipping.")
            return
            
        if mido is None:
            midi_logger.error("❌🚫🛑 [MIDI] Cannot start: mido missing.")
            return
            
        self._running = True
        if LOCAL_DEBUG:
            midi_logger.info("🎹🎼🚀 [MIDI] MIDI Engine Starting...")

        if self.run_bridge:
            try:
                # 1. Discovery
                info = self.get_port_info()
                
                # 2. Open ALL Inputs
                for name in sorted(list(set(info["inputs"]))):
                    try:
                        if LOCAL_DEBUG:
                            midi_logger.debug(f"🎹🎼🔍 [MIDI] Opening INPUT: {name}")
                        port = mido.open_input(name)
                        self.inports.append(port)
                        t = threading.Thread(target=self._midi_listen_loop, 
                                             args=(port,), daemon=True)
                        t.start()
                        self._listen_threads.append(t)
                        if LOCAL_DEBUG:
                            midi_logger.success(f"🎹🎼✅ [MIDI] INPUT READY: {name}")
                    except Exception as e:
                        midi_logger.error(f"❌🚫🛑 [MIDI] FAILED INPUT {name}: {e}")

                # 3. Open ALL Outputs
                for name in info["outputs"]:
                    try:
                        if LOCAL_DEBUG:
                            midi_logger.debug(f"🎹🎼🔍 [MIDI] Opening OUTPUT: {name}")
                        port = mido.open_output(name)
                        self.outports.append(port)
                        if LOCAL_DEBUG:
                            midi_logger.success(f"🎹🎼✅ [MIDI] OUTPUT READY: {name}")
                    except Exception as e:
                        midi_logger.error(f"❌🚫🛑 [MIDI] FAILED OUTPUT {name}: {e}")

                # 4. Broadcast Initial Status
                self._broadcast_status()

                if LOCAL_DEBUG:
                    midi_logger.success("🎹🎼✅ [MIDI] Engine fully operational.")

            except Exception as e:
                midi_logger.error(f"❌🚫🛑 [MIDI] Critical Start Error: {e}")

    def _broadcast_status(self):
        """Publishes active port list to the system state."""
        if self.state_cache_manager and self.run_bridge:
            active_in = [p.name for p in self.inports]
            active_out = [p.name for p in self.outports]
            self.state_cache_manager.handle_external_update(
                "OPEN-AIR/System/Status/MIDI/ActiveInputs", active_in, 
                source="MIDI"
            )
            self.state_cache_manager.handle_external_update(
                "OPEN-AIR/System/Status/MIDI/ActiveOutputs", active_out, 
                source="MIDI"
            )

    def stop(self):
        self._running = False
        if LOCAL_DEBUG:
            midi_logger.warning("🎹🎼🛑 [MIDI] Stopping MIDI Engine...")
        for p in self.inports: p.close()
        for p in self.outports: p.close()
        self.inports.clear()
        self.outports.clear()
        if LOCAL_DEBUG:
            midi_logger.info("🎹🎼👋 [MIDI] MIDI Engine Offline.")

    def _midi_listen_loop(self, port):
        """Background thread listening for a specific port."""
        from workers.Command_Router.protocol_router import ProtocolRouter
        router = ProtocolRouter.get_instance()
        if LOCAL_DEBUG:
            midi_logger.debug(f"🎹🎼👂 [MIDI] Listen Thread: {port.name}")

        while self._running:
            try:
                for msg in port.iter_pending():
                    if LOCAL_DEBUG:
                        midi_logger.trace(f"📥🎼📥 [MIDI] RAW RX [{port.name}]: {msg}")
                    
                    # 1. Transform (Pass port name for unique routing)
                    topic, val = self._map_midi_to_internal(msg, port.name)
                    
                    # ⚡ LOGICAL IDENTITY: device_id/channel (e.g. 32_0/3)
                    parts = topic.split('/')
                    dev_id = parts[2] if len(parts) > 2 else "unknown"
                    logical_guid = f"{dev_id}/{msg.channel}" if hasattr(msg, "channel") \
                                   else dev_id

                    # ⚡ ANTI-FEEDBACK SPEC: Define identity at transport ingress
                    meta = {
                        "midi_type": msg.type,
                        "guid": logical_guid,
                        "msg_type": "SPLICE_ACTION",
                        "origin_source": "MIDI"
                    }

                    # ⚡ HARDWARE LOCKING: Human is moving a fader/knob
                    with self._lock_mutex:
                        if msg.type in ['control_change', 'pitchwheel', 
                                      'aftertouch', 'note_on']:
                            self._hardware_locked_params.add(topic)
                        elif msg.type in ['note_off']:
                            if topic in self._hardware_locked_params: 
                                self._hardware_locked_params.remove(topic)

                    # 2. INGEST Hub (Internal Routing & Investigation)
                    router.ingest("MIDI", topic, val, meta)

                    # ⚡ RELEASE DELAY: For CC messages, release lock after inactivity.
                    if msg.type == 'control_change':
                        def _release_later(t=topic):
                            time.sleep(0.5) # 500ms inactivity release
                            with self._lock_mutex:
                                if t in self._hardware_locked_params: 
                                    self._hardware_locked_params.remove(t)
                        threading.Thread(target=_release_later, daemon=True).start()

                    # 3. Notify Local Dashboard
                    self._notify_monitor("RX", msg)

                    # 4. Update State Cache (Broadcasts to MQTT)
                    if self.state_cache_manager:
                        payload = {"val": val}
                        if hasattr(msg, "note"):
                            payload["note"] = msg.note
                            
                        # Propagate spec fields
                        self.state_cache_manager.handle_external_update(
                            topic, payload, source="MIDI", metadata=meta
                        )
            except Exception as e:
                midi_logger.error(f"❌🚫🛑 [MIDI] Listen Error on {port.name}: {e}")
            time.sleep(0.001)

    def _on_protocol_event(self, msg):
        """Callback for all router traffic. Handles MIDI mirroring and updates."""
        if not self._running: return
        
        source = msg.get("source", "UNKNOWN").upper()
        logical_source = msg.get("logical_source", source).upper()
        topic = str(msg.get("topic", ""))
        val = msg.get("val")
        meta = msg.get("meta", {})
        guid = msg.get("guid")

        # ⚡ ANTI-FEEDBACK SPEC: Unified Fields
        msg_type = msg.get("msg_type") or meta.get("msg_type", "SPLICE_ACTION")
        origin_source = msg.get("origin_source") or meta.get("origin_source", 
                                                         logical_source)

        # --- CASE 1: Port Status Updates (For UI Sync) ---
        if topic == "OPEN-AIR/System/Status/MIDI/ActiveInputs":
            real_val = val.get("val") if isinstance(val, dict) and "val" in val \
                       else val
            self._active_in_names = real_val if isinstance(real_val, list) else []
            return
        if topic == "OPEN-AIR/System/Status/MIDI/ActiveOutputs":
            real_val = val.get("val") if isinstance(val, dict) and "val" in val \
                       else val
            self._active_out_names = real_val if isinstance(real_val, list) else []
            return

        # --- CASE 2: MIDI Traffic Monitoring (For UI Feed) ---
        if not self.run_bridge:
            if logical_source == "MIDI":
                # Find the 'raw' MIDI payload
                target = val if isinstance(val, dict) and "raw" in val else meta
                if isinstance(target, dict) and "raw" in target:
                    if LOCAL_DEBUG:
                        midi_logger.trace(f"🎹🎼📺 [MIDI] UI Activity: "
                                         f"{target.get('port','Remote')}")
                    self._notify_monitor("RX", target)
            return

        # --- CASE 3: Internal -> External Sync (For MIDI Out) ---
        # Only if we are the bridge (Core) and it's not a reflection
        if self.run_bridge and source in ["GUI", "MQTT", "SNMP", "OSC", "SYSTEM"]:
            # ⚡ HARDWARE INTERACTION LOCK
            with self._lock_mutex:
                if topic in self._hardware_locked_params:
                    if LOCAL_DEBUG:
                        midi_logger.trace(f"🔒🎼🚫 [MIDI] LOCK: Dropping TX for "
                                         f"{topic} - Human touched hardware.")
                    return

            # ⚡ ANTI-FEEDBACK SPEC: The Golden Rule for Transports
            if msg_type == "LINK_FEEDBACK" and not msg.get("is_settled"):
                return
            if origin_source == "MIDI":
                return
            if source == "MQTT" and guid == app_constants.INSTANCE_GUID:
                return

            real_val = val.get("val") if isinstance(val, dict) and "val" in val \
                       else val
            midi_msg = self._map_internal_to_midi(topic, real_val)
            if midi_msg:
                if LOCAL_DEBUG:
                    midi_logger.debug(f"📤🎼📤 [MIDI] Sync: {topic}={real_val} "
                                     f"-> {midi_msg}")
                for port in self.outports:
                    try:
                        port.send(midi_msg)
                        self._notify_monitor("TX", f"[{port.name}] {str(midi_msg)}")
                    except Exception as e:
                        midi_logger.error(f"❌🚫🛑 [MIDI] TX Error on {port.name}: {e}")
                
                from workers.Command_Router.protocol_router import ProtocolRouter
                ProtocolRouter.get_instance().ingest("MIDI-TX", topic, real_val, {
                    "midi_raw": str(midi_msg),
                    # ⚡ ANTI-FEEDBACK SPEC: Propagate
                    "msg_guid": msg.get("msg_guid"),
                    "msg_type": msg_type,
                    "origin_source": origin_source
                })

    def _map_midi_to_internal(self, msg, port_name=None):
        m_type = msg.type
        m_chan = msg.channel if hasattr(msg, 'channel') else 0
        
        # Create a unique device identifier from the port name
        if port_name in self._dev_id_cache:
            dev_id = self._dev_id_cache[port_name]
        else:
            dev_id = "unknown"
            if port_name:
                match = re.search(r"(\d+:\d+)", port_name)
                if match:
                    dev_id = match.group(1).replace(":", "_")
                else:
                    dev_id = re.sub(r'[^a-zA-Z0-9]', '_', port_name).lower().strip('_')
            self._dev_id_cache[port_name] = dev_id
        
        base = f"OPEN-AIR/MIDI/{dev_id}/ch{m_chan}"
        
        if m_type == 'control_change':
            return f"{base}/cc{msg.control}", msg.value
        elif m_type in ['note_on', 'note_off']:
            return f"{base}/note{msg.note}", (msg.velocity if m_type == 'note_on' else 0)
        return f"{base}/{m_type}", 0

    def _map_internal_to_midi(self, topic, val):
        return None 
