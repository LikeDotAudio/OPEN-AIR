# Core/ptp_packet_parser.py
# Author: Anthony Peter Kuzub
# Version: 20260401.1200.1
#
# Description: Wrapper for High-Performance Rust PTP Packet Parser

import time
import sys
import os
from scapy.all import IP, UDP
from loguru import logger

# Add the hyphenated directory to sys.path temporarily to import compiler_hook
_rs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Methods", "oaPtpParser-rs")
if _rs_dir not in sys.path:
    sys.path.insert(0, _rs_dir)

import compiler_hook
compiler_hook.ensure_compiled()

import importlib
importlib.invalidate_caches()

try:
    import oaptpparser_rs
except ImportError as e:
    logger.critical("🚀❌ [FATAL] Rust PTP Parser module missing. Pure Rust mode is mandatory.")
    raise e

class PTPPacketParser:
    """Standardizes the extraction of PTP header fields into structured data using Rust."""

    @classmethod
    def tear_apart(cls, pkt, ptp_layer=None):
        """
        Extracts PTP fields, IPs, and timestamps into a flat dictionary via Rust.
        If `ptp_layer` is provided, we can still parse it, but we prefer raw bytes.
        """
        # If we didn't extract raw payload in ptp.py, do it here
        if pkt.haslayer(UDP):
            payload = bytes(pkt[UDP].payload)
            src_ip = pkt[IP].src if pkt.haslayer(IP) else "Unknown"
            dst_ip = pkt[IP].dst if pkt.haslayer(IP) else "Unknown"
            udp_port = pkt[UDP].dport
            
            # Offload heavy lifting to Rust
            return oaptpparser_rs.parse_packet(payload, src_ip, dst_ip, udp_port)
        
        return None
