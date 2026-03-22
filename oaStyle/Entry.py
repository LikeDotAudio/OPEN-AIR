# oaStyle/Entry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

"""
oaStyle/Entry.py - The sole orchestrator for the Styling Module.

Purpose:
This file is the public entry point for 'oaStyle'. It provides access to
UI themes and tools for applying styles to Tkinter applications.
"""

from .Core.style import THEMES, DEFAULT_THEME
from .Managers.theme_applier import apply_theme

def get_themes():
    """Returns the available themes."""
    return THEMES

def get_default_theme_name():
    """Returns the name of the default theme."""
    return DEFAULT_THEME

# Standardized exports
__all__ = [
    "THEMES",
    "DEFAULT_THEME",
    "apply_theme",
    "get_themes",
    "get_default_theme_name"
]
