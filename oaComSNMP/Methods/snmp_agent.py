# oaComSNMP/Methods/snmp_agent.py
# Author: Anthony Peter Kuzub
# Version: 20260331.1930.2
#
# Description: Pure Rust SNMP OID tree manager (No Python fallback).

LOCAL_DEBUG = True

from .oaSNMPAgent_rs.compiler_hook import ensure_compiled
ensure_compiled()
from .oaSNMPAgent_rs.oasnmpagent_rs import SnmpAgent as RustSnmpAgent

class SnmpAgent:
    """
    High-performance SNMP OID tree manager using Rust BTreeMap.
    MANDATORY Rust implementation.
    """
    def __init__(self):
        if LOCAL_DEBUG:
            print("📡🛠️🔗 [SNMP] Using PURE RUST agent.")
        self._agent = RustSnmpAgent()

    def update_oid(self, oid: str, value: str):
        self._agent.update_oid(oid, str(value))

    def get_oid(self, oid: str):
        return self._agent.get_oid(oid)

    def get_next(self, oid: str):
        return self._agent.get_next(oid)

    def clear(self):
        self._agent.clear()
