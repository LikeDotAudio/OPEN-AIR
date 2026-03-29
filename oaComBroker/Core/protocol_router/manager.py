# oaComBroker/Core/protocol_router/manager.py
#
# High-level Orchestrator Proxy for the Protocol Router.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260328.1610.1
#
# Description:
# This file serves as a high-level Manager proxy for the ProtocolRouter logic 
# located in the Core partition. It maintains architectural consistency by
# providing a familiar import path for legacy modules while adhering to the
# Core/UI separation required by the OPEN-AIR standards.
#
# Partitioned Architecture (Core vs UI):
# This is part of the 'Core' protocol_router package. It provides the 
# high-level interface (Manager) for the internal routing logic.
#
# Architectural Role:
# - Acts as a bridge between the 'Managers' conceptual layer and 'Core' logic.
# - Ensures that modules requiring the ProtocolRouter receive the correct 
#   Singleton instance.

from .router import ProtocolRouter

# Export the class to maintain backward compatibility with early 2025 modules.
__all__ = ["ProtocolRouter"]
