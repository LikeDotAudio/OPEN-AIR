# oaGui/Workers/transparency/__init__.py
# Author: Gemini CLI
# Version: 20260501.1000.1
# Description: Exposes public API for the transparency module.

__all__ = [
    "TransparencyConfig",
    "BackgroundSlicer",
    "TransparencyManager",
]

from oaGui.Methods.transparency_config_parser import TransparencyConfigParser as TransparencyConfig
from oaGui.Workers.transparency.background_slicer import BackgroundSlicer
from oaGui.Workers.transparency.transparency import TransparencyManager
