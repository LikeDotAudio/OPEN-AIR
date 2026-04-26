# Methods/schema_utils.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Utility functions for schema manipulation and normalization.

from oaGui.Constants.schema_defaults import ANCHOR_MAP, LEXICON


def deep_merge(target, source):
    """Deep merges source dict into target dict without erasing nested blocks."""
    for k, v in source.items():
        if (isinstance(v, dict) and k in target and
            isinstance(target[k], dict)):
            deep_merge(target[k], v)
        else:
            target[k] = v
    return target

def expand_abbreviations(data):
    """Recursively translates Lexicon Abbreviations to Engine Keys."""
    if not isinstance(data, dict):
        return data

    new_data = {}
    for k, v in data.items():
        if isinstance(v, dict):
            v = expand_abbreviations(v)

        target_key = LEXICON.get(k, k)
        new_data[target_key] = v
    return new_data

def get_styled_val(key_list, config, style_block, cosmetics, default=None):
    """Probes multiple blocks for a style value."""
    colors = cosmetics.get("colors", {})
    for k in key_list:
        if k in style_block: return style_block[k]
        if k in config: return config[k]
        if k in colors: return colors[k]
        if k in cosmetics: return cosmetics[k]
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
