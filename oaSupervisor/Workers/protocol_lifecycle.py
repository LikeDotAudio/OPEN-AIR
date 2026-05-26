# oaSupervisor/Workers/protocol_lifecycle.py
#
# Centralised protocol manager init + shutdown. The supervisor only DISCOVERS
# and REGISTERS protocols — it never starts their services. Starting protocol
# services in the supervisor would create "ghost" services competing for ports
# with the Core partition that owns them.

import sys
import traceback


def initialize_protocol_manager(log):
    """Discover + register protocols in the supervisor (without starting any service)."""
    log("Initializing Communication Protocol Manager (Supervisor Mode)...")
    from oaComProtocols.oaComManager.Entry import ComProtocolManager
    from oaConfigurationManager.FileReaders.config_reader import Config
    try:
        config = Config.get_instance()
        protocol_manager = ComProtocolManager.get_instance(config=config)
        protocol_manager.discover_and_register_protocols()
        protocol_manager.initialize_common_dependencies()
        log("Protocol Manager initialized. Services will be launched by child partitions.")
        return protocol_manager
    except Exception as e:
        log(f"🛑 CRITICAL ERROR during protocol initialization: {e}")
        traceback.print_exc()
        if 'protocol_manager' in locals() and protocol_manager:
            try: protocol_manager.stop_all()
            except Exception: pass
        sys.exit(1)


def shutdown_protocol_manager(log):
    """Stop all registered protocols on the way out."""
    log("Shutting down communication protocols...")
    try:
        from oaComProtocols.oaComManager.Entry import ComProtocolManager
        pm = ComProtocolManager.get_instance()
        if pm:
            pm.stop_all()
        else:
            log("⚠️ Protocol manager not initialized, cannot stop protocols.")
    except Exception as e:
        log(f"❌ Error during protocol shutdown: {e}")
