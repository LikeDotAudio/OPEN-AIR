# Core/protocol_router/__init__.py
#
# Modular package definition for the Protocol Router engine.
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
# Version 20260328.1450.1
#
# Description:
# This package encapsulates the Protocol Router and its associated subsystems 
# (Ingest, DPI, Strategy, Dispatch, Monitoring). It provides the core 
# multiplexing logic required for the OPEN-AIR partitioned architecture.

from .router import ProtocolRouter

__all__ = ["ProtocolRouter"]
