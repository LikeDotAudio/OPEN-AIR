# protocol_router/monitor.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Monitoring and Firehose Management for the Protocol Router.

import threading
import orjson
from .constants import SOURCE_DESCRIPTIONS, EMOJI_TO_WORD, app_constants

class Monitor:
    """
    Manages the firehose buffer and provides investigation tools.
    """
    def __init__(self, local_guid):
        self.local_guid = local_guid
        self.firehose = []
        self._firehose_lock = threading.Lock()
        self._observers = []

    def register_cache_observer(self, callback):
        """Registers a callback for UI/Monitoring broadcast."""
        self._observers.append(callback)

    def remove_observer(self, callback):
        """Unregisters a callback."""
        if callback in self._observers:
            self._observers.remove(callback)

    def append_to_firehose(self, msg):
        """Maintains the firehose rolling buffer."""
        with self._firehose_lock:
            self.firehose.insert(0, msg)
            if len(self.firehose) > 2000:
                self.firehose.pop()

    def get_splink_relationship(self, msg_ts):
        """Correlates a message with its Splink partner."""
        with self._firehose_lock:
            match = next((m for m in self.firehose if 
                          f"{m['ts']:.6f}" == msg_ts or m['ts'] == msg_ts), None)
            
            if not match:
                return None, None
            
            s_id = (match["meta"].get("splink_id") or 
                    match["meta"].get("splinker_source"))
            
            if not s_id:
                return None, None
            
            is_active = match["meta"].get("splink_active")
            
            if is_active:
                candidates = [m for m in self.firehose if 
                             m["meta"].get("splinker_source") == s_id]
            else:
                candidates = [m for m in self.firehose if 
                             m["meta"].get("splink_id") == s_id]
        
        if not candidates:
            return (match["ts"] if is_active else None), (None if is_active else match["ts"])
            
        partner = min(candidates, key=lambda m: abs(m["ts"] - match["ts"]))
        
        if is_active:
            return match["ts"], partner["ts"]
        else:
            return partner["ts"], match["ts"]

    def get_dpi_report(self, msg_ts):
        """Generates a human-readable investigation report for a specific packet."""
        match = None
        with self._firehose_lock:
            match = next((m for m in self.firehose if 
                          f"{m['ts']:.6f}" == msg_ts or m['ts'] == msg_ts), None)
        
        if not match:
            return "Packet not found in firehose buffer."

        report = []
        source = match['source']
        src_desc = SOURCE_DESCRIPTIONS.get(source, f"❓ [{source}] - Unknown origin.")
        
        report.append("╔════════════ PACKET INVESTIGATION REPORT ════════════╗")
        report.append(f"  TIME (UTP) : {match['ts']}")
        
        p_id = match.get("partition", "UNKNOWN")
        is_local_session = (match['guid'] == self.local_guid)
        is_local_partition = (p_id == app_constants.PARTITION_ID)
        
        p_desc = f"{p_id} ({'HERE' if is_local_partition else 'REMOTE'})"
        s_desc = f"{match['guid']} ({'THIS SESSION' if is_local_session else 'REMOTE'})"
        
        report.append(f"  SESSION    : {s_desc}")
        report.append(f"  PARTITION  : {p_desc}")
        report.append("╟──────────────────────────────────────────────────────╢")
        report.append(f"  SOURCE     : {src_desc}")
        report.append(f"  TOPIC/PATH : {match['topic']}")
        report.append(f"  RAW VALUE  : {match['val']}")
        report.append("╟──────────────────────────────────────────────────────╢")

        strat = match.get("strategy", "BROADCAST")
        report.append(f"  STRATEGY   : {strat}")
        
        lifecycle_parts = []
        for char in strat:
            if char in EMOJI_TO_WORD:
                lifecycle_parts.append(f"[{EMOJI_TO_WORD[char]}]")
        
        if lifecycle_parts:
            if "[PUSH]" in lifecycle_parts:
                p_idx = lifecycle_parts.index("[PUSH]")
                source_part = " ".join(lifecycle_parts[:p_idx])
                dest_part = " ".join(lifecycle_parts[p_idx+1:])
                lifecycle_str = f"{source_part} -> PUSH -> {dest_part}"
            else:
                lifecycle_str = " -> ".join(lifecycle_parts)
            report.append(f"  LIFECYCLE  : {lifecycle_str}")
        
        if match["meta"]:
            report.append("╟── DEEP PACKET INSPECTION (DPI) ──────────────────────╢")
            for k, v in match["meta"].items():
                if k in ["ui_tags"]: continue
                k_disp = k.replace("_", " ").upper()
                prefix = "🔬 "
                if "mib" in k.lower(): prefix = "Ⓢ 🔍 "
                if "osc" in k.lower(): prefix = "🅾️ 🔍 "
                if "midi" in k.lower(): prefix = "🎹 🔍 "
                if "mutation" in k.lower(): prefix = "🚨 ⚡ "
                report.append(f"  {prefix}{k_disp}: {v}")
        
        try:
            if isinstance(match['val'], dict):
                report.append("╟── PAYLOAD DISSECTION ────────────────────────────────╢")
                pretty_json = orjson.dumps(match['val'], 
                                           option=orjson.OPT_INDENT_2).decode()
                report.append(f"{pretty_json}")
        except:
            pass
        
        report.append("╚════════════════════════ END ════════════════════════╝")
        return "\n".join(report)

    def broadcast_to_observers(self, msg):
        """Notifies all registered observers about a new message."""
        for cb in self._observers:
            try:
                cb(msg)
            except:
                pass
