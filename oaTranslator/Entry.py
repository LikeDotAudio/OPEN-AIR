# oaTranslator/Entry.py
#
# The sole orchestrator for the Translator Module. It exposes the public API 
# for YAK command translation and trigger handling.
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
# Version 20260406.2005.1

"""
oaTranslator/Entry.py - The sole orchestrator for the Translator Module.
"""

from .Managers.yak_translator import YakTranslator
from .Managers.yak_trigger_handler import *

__all__ = [
    "YakTranslator",
    "YakTriggerHandler"
]
