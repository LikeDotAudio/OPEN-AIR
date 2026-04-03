# oaComSNMP/Methods/snmp_agent.py
# Author: Anthony Peter Kuzub
# Version: 20260331.1930.2
#
# Description: Pure Rust SNMP OID tree manager (No Python fallback).

LOCAL_DEBUG = True

import logging
from .oaSNMPAgent_rs.compiler_hook import ensure_compiled

try:
    ensure_compiled()
    from oasnmpagent_rs import SnmpAgent as RustSnmpAgent
    HAS_RUST = True
except ImportError:
    logging.warning("⚠️ [SNMP] oasnmpagent_rs not found. SNMP functionality will be restricted.")
    HAS_RUST = False
except Exception as e:
    logging.error(f"❌ [SNMP] Failed to initialize Rust SNMP Agent: {e}")
    HAS_RUST = False

LOCAL_DEBUG = True

class SnmpAgent:
    """
    High-performance SNMP OID tree manager using Rust BTreeMap.
    MANDATORY Rust implementation.
    """
    def __init__(self):
        self._agent = None
        if not HAS_RUST:
            return

        if LOCAL_DEBUG:
            print("📡🛠️🔗 [SNMP] Using PURE RUST agent.")
        try:
            self._agent = RustSnmpAgent()
        except Exception as e:
            logging.error(f"❌ [SNMP] Rust SNMP agent instantiation failed: {e}")
            self._agent = None

    def update_oid(self, oid: str, value: str):
        if self._agent:
            self._agent.update_oid(oid, str(value))

    def get_oid(self, oid: str):
        if self._agent:
            return self._agent.get_oid(oid)
        return None

    def get_next(self, oid: str):
        if self._agent:
            return self._agent.get_next(oid)
        return None

    def clear(self):
        if self._agent:
            self._agent.clear()

