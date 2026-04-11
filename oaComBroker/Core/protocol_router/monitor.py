# Core/protocol_router/monitor.py
#
# Monitoring and Firehose Management for the Protocol Router.
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
# Version 20260328.1430.1
#
# Description:
# The Monitor class provides deep observability into the ProtocolRouter's
# traffic. It maintains a rolling "firehose" buffer for forensic analysis
# and implements a broadcast system for UI and telemetry observers.
#
# Architectural Role:
# - Serves as the primary data source for system-wide telemetry.
# - Provides forensic reporting via Deep Packet Inspection (DPI).
# - Correlates patched "Splink" relationships across network sessions.

from collections import deque
import threading
import orjson
import time
from .constants import SOURCE_DESCRIPTIONS, EMOJI_TO_WORD, app_constants
from oaLogging.Methods.matrix_gate import matrix_log

class Monitor:
    """
    Manages the firehose buffer and provides forensic investigation tools.
    
    The Monitor acts as a passive observer within the router, capturing 
    every normalized packet for auditing and UI visualization.
    """
    def __init__(self, local_guid):
        """
        Initializes the monitor with a rolling buffer.
        
        Args:
            local_guid (str): The unique ID of the local router instance.
        """
        self.local_guid = local_guid
        # ⚡ OPTIMIZATION: Use deque with maxlen for O(1) appends and auto-eviction.
        self.firehose = deque(maxlen=2000)
        self._firehose_lock = threading.Lock()
        self._observers = []

        # Telemetry Initialization
        self._msg_count = 0
        self._byte_count = 0
        self._last_telemetry_ts = time.time()
        self._telemetry = {
            "pps": 0,
            "bps": 0,
            "latency_ms": 0,
            "total_msgs": 0
        }

    def register_cache_observer(self, callback):
        """
        Registers a callback for real-time telemetry broadcast.
        
        Args:
            callback (fn): A function to receive every processed message.
        """
        self._observers.append(callback)

    def remove_observer(self, callback):
        """
        Unregisters a telemetry observer.
        """
        if callback in self._observers:
            self._observers.remove(callback)

    def append_to_firehose(self, msg):
        """
        Maintains the rolling "firehose" buffer (last 2000 packets).
        
        Args:
            msg (dict): The normalized message packet to store.
        """
        with self._firehose_lock:
            # ⚡ O(1) append to the left
            self.firehose.appendleft(msg)

        # Update Telemetry Counters
        self._msg_count += 1
        # ⚡ OPTIMIZATION: Use a cheap estimation instead of orjson.dumps on every message.
        # This reduces CPU usage in the critical ingest path.
        self._byte_count += 256 # Assume 256 bytes per packet on average

        # Calculate Latency (Ingest TS vs Current TS)
        if "ts" in msg:
            latency = (time.time() - msg["ts"]) * 1000
            self._telemetry["latency_ms"] = (self._telemetry["latency_ms"] * 0.9) + (latency * 0.1)

        # Publish telemetry once per second
        now = time.time()
        if now - self._last_telemetry_ts >= 1.0:
            self._publish_telemetry(now)

    def _publish_telemetry(self, now):
        elapsed = now - self._last_telemetry_ts
        if elapsed <= 0: return

        self._telemetry["pps"] = int(self._msg_count / elapsed)
        self._telemetry["bps"] = int((self._byte_count * 8) / elapsed)
        self._telemetry["total_msgs"] += self._msg_count
        
        # Reset interval counters
        self._msg_count = 0
        self._byte_count = 0
        self._last_telemetry_ts = now
        
        # Broadcast to observers (UI)
        telemetry_msg = {
            "ts": now,
            "source": "SYSTEM",
            "topic": "OPEN-AIR/System/Monitor/Telemetry",
            "val": self._telemetry.copy(),
            "meta": {"msg_type": "TELEMETRY", "is_settled": True}
        }
        self.broadcast_to_observers(telemetry_msg)

    def get_splink_relationship(self, msg_ts):
        """
        Correlates a message with its connected "Splink" partner.
        
        Splinks represent logical patches between topics (e.g., Fader A
        controls EQ Gain B). This method identifies the partner message
        in the firehose based on the metadata links.
        
        Args:
            msg_ts (float/str): The timestamp of the message to investigate.
            
        Returns:
            tuple: (source_ts, dest_ts) or (None, None).
        """
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
        """
        Generates a human-readable forensic report for a specific packet.
        
        Constructs a visual ASCII report detailing the packet's origin,
        session ID, routing strategy, and DPI-enriched metadata.
        
        Args:
            msg_ts (float/str): The timestamp of the packet to report on.
            
        Returns:
            str: The formatted report.
        """
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
        """
        Notifies all registered observers about a new message.
        """
        for cb in self._observers:
            try:
                cb(msg)
            except Exception as e:
                matrix_log("comms", "broker", "broadcast_to_observers", f"BROADCAST ERROR to {cb}: {e}", "ERROR")

    def shutdown(self):
        """
        ⚡ V3.1.29 GRACEFUL SHUTDOWN: Clears all observers to prevent 
        'main thread is not in main loop' errors during system teardown.
        """
        self._observers = []
        matrix_log("comms", "broker", "shutdown", "Monitor observers cleared.", "DEBUG")
