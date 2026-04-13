# Core/ptp_packet_parser.py
# Author: Anthony Peter Kuzub
# Version: 20260401.1200.1
#
# Description: Wrapper for High-Performance Rust PTP Packet Parser

import time
import sys
import os
from loguru import logger

try:
    from oaRustCore import oa_ptp_parser_rs as oaptpparser_rs
    HAS_RUST = True
except ImportError:
    logger.warning("⚠️ [PTP] oaptpparser_rs not found. PTP parsing will be disabled.")
    HAS_RUST = False
except Exception as e:
    logger.error(f"❌ [PTP] Failed to initialize Rust PTP Parser: {e}")
    HAS_RUST = False

class PTPPacketParser:
    """Standardizes the extraction of PTP header fields into structured data using Rust."""

    @classmethod
    def tear_apart(cls, pkt, ptp_layer=None):
        """
        Extracts PTP fields, IPs, and timestamps into a flat dictionary via Rust.
        If `ptp_layer` is provided, we can still parse it, but we prefer raw bytes.
        """
        if not HAS_RUST:
            return None

        from scapy.all import IP, UDP

        # If we didn't extract raw payload in ptp.py, do it here
        if pkt.haslayer(UDP):
            payload = bytes(pkt[UDP].payload)
            src_ip = pkt[IP].src if pkt.haslayer(IP) else "Unknown"
            dst_ip = pkt[IP].dst if pkt.haslayer(IP) else "Unknown"
            udp_port = pkt[UDP].dport

            # Offload heavy lifting to Rust
            try:
                return oaptpparser_rs.parse_packet(payload, src_ip, dst_ip, udp_port)
            except Exception as e:
                logger.error(f"❌ [PTP] Rust parsing failed: {e}")
                return None

        return None

