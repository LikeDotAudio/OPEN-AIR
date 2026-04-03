# oaPTP/Tests/test_ptp_parser_rust.py
#
# Tests for the PTP Packet Parser (Rust implementation).
#
# Author: Anthony Peter Kuzub
# Version: 20260401.1000.1

import unittest
from unittest.mock import MagicMock
from scapy.all import IP, UDP
from oaPTP.Core.ptp_packet_parser import PTPPacketParser

class MockPkt:
    def __init__(self, payload, src_ip="192.168.1.10", dst_ip="224.0.1.129", dport=319):
        self.payload = payload
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.dport = dport

    def haslayer(self, layer_type):
        return layer_type in [IP, UDP]

    def __getitem__(self, layer_type):
        if layer_type == IP:
            return MagicMock(src=self.src_ip, dst=self.dst_ip)
        if layer_type == UDP:
            return MagicMock(payload=self.payload, dport=self.dport)
        return MagicMock()

class TestPtpParserRust(unittest.TestCase):
    def test_rust_ptp_parsing_sync(self):
        """Test Sync message parsing via Rust."""
        try:
            import oaptpparser_rs
        except ImportError:
            self.skipTest("Rust oaptpparser_rs not installed.")

        # Minimal PTP Sync Packet (34 bytes minimum)
        # Byte 0: messageType 0 (Sync)
        # Byte 20-29: Port ID
        # Byte 30-31: Sequence ID
        payload = bytearray(34)
        payload[0] = 0x00 # Sync
        payload[4] = 0x01 # Domain 1
        payload[30] = 0x01
        payload[31] = 0x2C # Seq 300
        
        # Port Identity: 01:02:03:04:05:06:07:08 + Port 123
        payload[20:28] = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        payload[28] = 0x00
        payload[29] = 0x7B # Port 123 (0x7B)

        pkt = MockPkt(bytes(payload))
        data = PTPPacketParser.tear_apart(pkt)

        self.assertIsNotNone(data)
        self.assertEqual(data["message_type"], "Sync")
        self.assertEqual(data["domain"], 1)
        self.assertEqual(data["sequence_id"], 300)
        self.assertEqual(data["clock_identity"], "01:02:03:04:05:06:07:08 (Port 123)")
        self.assertEqual(data["source_ip"], "192.168.1.10")

    def test_rust_ptp_parsing_announce(self):
        """Test Announce message parsing via Rust."""
        try:
            import oaptpparser_rs
        except ImportError:
            self.skipTest("Rust oaptpparser_rs not installed.")

        payload = bytearray(34)
        payload[0] = 0x0B # Announce (11)
        payload[4] = 0x02 # Domain 2
        payload[30] = 0x03
        payload[31] = 0x04 # Seq 772

        pkt = MockPkt(bytes(payload))
        data = PTPPacketParser.tear_apart(pkt)

        self.assertEqual(data["message_type"], "Announce")
        self.assertEqual(data["domain"], 2)
        self.assertEqual(data["sequence_id"], 772)

if __name__ == '__main__':
    unittest.main()
