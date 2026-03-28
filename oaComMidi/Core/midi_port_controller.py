# Core/midi_port_controller.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from loguru import logger

try: import mido
except ImportError: mido = None

class MIDIPortController:
    """Manages discovery and lifecycle of MIDI input and output ports."""

    def __init__(self, midi_logger):
        self.logger = midi_logger
        self.inports, self.outports = [], []

    def get_port_info(self, run_bridge, active_in_cache, active_out_cache):
        if mido is None: return {"error": "mido library missing"}
        try:
            inputs, outputs = mido.get_input_names(), mido.get_output_names()
            return {
                "inputs": inputs, "outputs": outputs,
                "active_in": [p.name for p in self.inports] if run_bridge else active_in_cache,
                "active_out": [p.name for p in self.outports] if run_bridge else active_out_cache,
                "error": None
            }
        except Exception as e:
            self.logger.error(f"❌ MIDI Scan Failed: {e}"); return {"error": str(e)}

    def open_all(self, info, listen_loop_cb):
        """Opens all detected input and output ports."""
        threads = []
        for name in sorted(list(set(info["inputs"]))):
            try:
                p = mido.open_input(name); self.inports.append(p)
                import threading
                t = threading.Thread(target=listen_loop_cb, args=(p,), daemon=True); t.start()
                threads.append(t); self.logger.success(f"🎹 INPUT READY: {name}")
            except Exception as e: self.logger.error(f"❌ FAILED INPUT {name}: {e}")

        for name in info["outputs"]:
            try:
                p = mido.open_output(name); self.outports.append(p)
                self.logger.success(f"🎹 OUTPUT READY: {name}")
            except Exception as e: self.logger.error(f"❌ FAILED OUTPUT {name}: {e}")
        return threads

    def close_all(self):
        for p in self.inports + self.outports:
            try:
                p.close()
            except Exception as e:
                self.logger.warning(f"🎹 Warning: Failed to close MIDI port {p.name if hasattr(p, 'name') else 'unknown'}: {e}")
        self.inports.clear(); self.outports.clear()
