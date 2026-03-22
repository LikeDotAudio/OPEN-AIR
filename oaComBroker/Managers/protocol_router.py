# Managers/protocol_router.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: BACKWARD COMPATIBILITY PROXY

from ..Core.protocol_router.router import ProtocolRouter

# Ensure that external modules can still access the class as if it was in this file.
__all__ = ["ProtocolRouter"]
