# oaComMidi/Core/midi_port_controller.py
#
# Low-level discovery and lifecycle management for MIDI ports.
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

from loguru import logger
from oaLogging.Methods.matrix_gate import matrix_log

try: import mido
except ImportError: mido = None

import os
# ⚡ SAFETY: Skip real hardware in restricted environments
if os.environ.get("OPEN_AIR_SKIP_REAL_MIDI") == "1":
    mido = None

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
                threads.append(t)
                matrix_log("core", "midi", "open_all", f"🎹 INPUT READY: {name}", "SUCCESS")
            except Exception as e: 
                self.logger.error(f"❌ FAILED INPUT {name}: {e}")

        for name in info["outputs"]:
            try:
                p = mido.open_output(name); self.outports.append(p)
                matrix_log("core", "midi", "open_all", f"🎹 OUTPUT READY: {name}", "SUCCESS")
            except Exception as e: 
                self.logger.error(f"❌ FAILED OUTPUT {name}: {e}")
        return threads

    def close_all(self):
        for p in self.inports + self.outports:
            try:
                p.close()
            except Exception as e:
                self.logger.warning(f"🎹 Warning: Failed to close MIDI port {p.name if hasattr(p, 'name') else 'unknown'}: {e}")
        self.inports.clear(); self.outports.clear()
