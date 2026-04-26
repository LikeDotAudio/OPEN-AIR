# oaGui/Core/transparency/__init__.py
# Author: Gemini CLI
# Version: 20260404.1.0
# Description: Exposes public API for the transparency module.

__all__ = [
    "TransparencyConfig",
    "BackgroundSlicer",
    "TransparencyManager",
]

from .transparency import BackgroundSlicer, TransparencyConfig, TransparencyManager
