# workers/Command_Router/protocol_router.py
#
# BACKWARD COMPATIBILITY PROXY
# This file is preserved to support existing imports while the core logic
# has been moved to the modular 'protocol_router' package.
#
# Original Author: Anthony Peter Kuzub
# Modularized: Saturday, March 14, 2026

from ..Core.protocol_router.router import ProtocolRouter

# Ensure that external modules can still access the class as if it was in this file.
__all__ = ["ProtocolRouter"]
