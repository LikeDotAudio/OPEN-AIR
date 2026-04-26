# oaComProtocols.oaComSNMP/Methods/snmp_utils.py
#
# Utility functions for SNMP node identification and descriptor generation.
#
# Author: Anthony Peter Kuzub (Contributor to this project)
# Blog: www.Like.audio
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260329.1040.1

import re
import zlib
from pathlib import Path

# Global map: "clean/path/prefix" -> "numerical_node_id"
_clean_to_num_map = {}

def initialize_oid_map(display_root):
    """
    Crawls the display directory to build a mapping of clean topics to sorting numbers.
    Aligns with MQTT topic generation by stripping layout tokens (left, right, etc.).
    Example: 'oaGui/Assets/left_50/top_100/0_Spectrum' -> {'Spectrum': '0'}
    """
    global _clean_to_num_map
    _clean_to_num_map.clear()

    root = Path(display_root)
    if not root.exists(): return

    # ⚡ ALIGNMENT: Tokens to strip from the clean path to match MQTT topics
    LAYOUT_TOKENS = ["display", "gui", "left", "right", "top", "bottom", "oagui", "assets"]

    for path in root.rglob("*"):
        if not path.is_dir(): continue

        # Build the clean path relative to display root
        rel_parts = path.relative_to(root).parts

        # Trace the path to build clean vs numerical mapping
        current_clean_path = []
        for p in rel_parts:
            # ⚡ CLEAN: Strip numeric prefix/suffix (e.g. '1_Router' -> 'Router')
            clean = re.sub(r"^(\d+)[_-]?", "", p)
            clean = re.sub(r"[_-]?(\d+)$", "", clean).replace(" ", "_")

            # ⚡ ALIGNMENT: Skip structural layout tokens
            if clean.lower() in LAYOUT_TOKENS or not clean:
                continue

            # Extract sorting number for OID assignment
            num_match = re.search(r"(\d+)", p)
            num = num_match.group(1) if num_match else None

            current_clean_path.append(clean)
            clean_str = "/".join(current_clean_path)

            if num:
                _clean_to_num_map[clean_str] = num

def get_snmp_node_id(path_parts):
    """
    Returns the numerical OID node ID for a given path context.
    Uses the pre-built crawler map to find folder sorting numbers.
    """
    if not path_parts: return "1"

    # 1. Check the crawler map for a match
    clean_path = "/".join(path_parts)
    if clean_path in _clean_to_num_map:
        return _clean_to_num_map[clean_path]

    # 2. Fallback: Deterministic 16-bit hash for non-folder parts (JSON keys)
    h_int = (zlib.crc32(clean_path.lower().encode()) & 0xFFFF)
    return str(h_int if h_int > 0 else 1)

def get_snmp_descriptor(path_parts):
    """
    Builds a unique, descriptive SMIv2 descriptor from a clean path.
    Uses camelCase path parts to stay under 64 characters.
    Example: OPEN-AIR/Mixing/Faders/Level -> mixingFadersLevela1b2
    """
    if not path_parts: return "v1"

    # ⚡ SMIv2 REQUIREMENT: Must start with lowercase letter, use only [a-zA-Z0-9]
    # Max length is technically 64 characters.

    clean_parts = []
    for p in path_parts:
        # Strip everything but alphanumeric
        c = re.sub(r"[^a-zA-Z0-9]", "", p)
        if not c: continue
        # CamelCase: first part lowercase, others capitalized
        if not clean_parts:
            clean_parts.append(c[0].lower() + c[1:])
        else:
            clean_parts.append(c[0].upper() + c[1:])

    if not clean_parts:
        clean_parts = ["node"]

    # Join parts to form the base name
    base_name = "".join(clean_parts)

    # 4-character deterministic path hash for global uniqueness
    full_path = "/".join(path_parts).lower()
    h_str = hex(zlib.crc32(full_path.encode()) & 0xffffffff)[2:6].zfill(4)

    # Enforce SMIv2 length limit (64 chars)
    # [BASE_NAME][HASH] = max 64. So base_name max 60.
    if len(base_name) > 60:
        base_name = base_name[:60]

    return f"{base_name}{h_str}"
