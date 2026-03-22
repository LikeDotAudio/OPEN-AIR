# Core/ptp_packet_parser.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import time
from scapy.all import IP, UDP

class PTPPacketParser:
    """Standardizes the extraction of PTP header fields into structured data."""

    MSG_TYPES = {
        0: "Sync", 1: "Delay_Req", 2: "Pdelay_Req", 3: "Pdelay_Resp",
        8: "Follow_Up", 9: "Delay_Resp", 10: "Pdelay_Resp_Follow_Up",
        11: "Announce", 12: "Signaling", 13: "Management"
    }

    @classmethod
    def tear_apart(cls, pkt, ptp_layer):
        """Extracts PTP fields, IPs, and timestamps into a flat dictionary."""
        try: m_id = ptp_layer.messageType
        except: m_id = -1
        
        m_type = cls.MSG_TYPES.get(m_id, f"Unknown ({m_id})")
        domain = getattr(ptp_layer, "domainNumber", 0)
        seq_id = getattr(ptp_layer, "sequenceId", 0)
        port_id = getattr(ptp_layer, "sourcePortIdentity", b"")

        return {
            "timestamp": time.time(),
            "source_ip": pkt[IP].src if IP in pkt else "Unknown",
            "dest_ip": pkt[IP].dst if IP in pkt else "Unknown",
            "udp_port": pkt[UDP].dport,
            "message_type": m_type,
            "domain": domain,
            "sequence_id": seq_id,
            "clock_identity": cls.format_clock_id(port_id),
        }

    @staticmethod
    def format_clock_id(raw):
        """Converts raw sourcePortIdentity bytes into a readable clock string."""
        if isinstance(raw, bytes) and len(raw) >= 10:
            return f"{raw[:8].hex(':')} (Port {int.from_bytes(raw[8:], 'big')})"
        return str(raw)
