# oaGui/FileReaders/standardizers/schema_utils.py
# Author: Anthony Peter Kuzub
# Version: 1.0.1
#
# Description: Utility functions for schema manipulation and normalization.

from oaGui.Constants.schema_defaults import ANCHOR_MAP, LEXICON


def deep_merge(target, source):
    """Deep merges source dict into target dict without erasing nested blocks."""
    for key, value in source.items():
        if (isinstance(value, dict) and key in target and
            isinstance(target[key], dict)):
            deep_merge(target[key], value)
        else:
            target[key] = value
    return target

def expand_abbreviations(data):
    """Recursively translates Lexicon Abbreviations to Engine Keys."""
    if not isinstance(data, dict):
        return data

    new_data = {}
    for key, value in data.items():
        if isinstance(value, dict):
            value = expand_abbreviations(value)

        target_key = LEXICON.get(key, key)
        new_data[target_key] = value
    return new_data

def get_styled_val(key_list, config, style_block, cosmetics, default=None):
    """Probes multiple blocks for a style value."""
    colors = cosmetics.get("colors", {})
    for key in key_list:
        if key in style_block: return style_block[key]
        if key in config: return config[key]
        if key in colors: return colors[key]
        if key in cosmetics: return cosmetics[key]
    return default

def calculate_sticky(geometry):
    """Translates Semantic Layout Model (Align/Anchor/Stretch) into Tkinter sticky bits."""
    sticky_parts = set()
    stretch = str(geometry.get("stretch", "")).lower()
    anchor = str(geometry.get("anchor", "")).lower()

    if any(p in ["width", "fill", "nsew"] for p in stretch.split()):
        sticky_parts.update(["e", "w"])
    if any(p in ["height", "fill", "nsew"] for p in stretch.split()):
        sticky_parts.update(["n", "s"])

    for p in anchor.split():
        if p in ANCHOR_MAP:
            sticky_parts.add(ANCHOR_MAP[p])

    return "".join(sorted(list(sticky_parts)))
