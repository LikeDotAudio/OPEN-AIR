# Core/ptp_packet_schema.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

try:
    from scapy.all import (
        UDP,
        BitField,
        ByteField,
        LongField,
        Packet,
        ShortField,
        StrFixedLenField,
        XShortField,
        bind_layers,
    )
    try:
        from scapy.contrib.ptp import PTP
        SCAPY_AVAILABLE = True
    except ImportError:
        class PTP(Packet):
            """Defines the PTP (Precision Time Protocol) packet structure if scapy contrib is missing."""
            name = "PTP"
            fields_desc = [
                BitField("transportSpecific", 0, 4), BitField("messageType", 0, 4),
                BitField("reserved", 0, 4), BitField("versionPTP", 2, 4),
                ShortField("messageLength", 34), ByteField("domainNumber", 0),
                ByteField("reserved1", 0), XShortField("flagField", 0),
                LongField("correctionField", 0), ByteField("reserved2", 0),
                ByteField("reserved3", 0), ByteField("reserved4", 0),
                ByteField("reserved5", 0), StrFixedLenField("sourcePortIdentity", b"\x00"*10, 10),
                ShortField("sequenceId", 0), ByteField("controlField", 0),
                ByteField("logMessageInterval", 0)
            ]
            def guess_payload_class(self, payload): return Packet.guess_payload_class(self, payload)
        SCAPY_AVAILABLE = True

    # Bind PTP to UDP ports 319 (event) and 320 (general)
    bind_layers(UDP, PTP, dport=319); bind_layers(UDP, PTP, dport=320)
    bind_layers(UDP, PTP, sport=319); bind_layers(UDP, PTP, sport=320)
except ImportError:
    SCAPY_AVAILABLE = False
    PTP = None
