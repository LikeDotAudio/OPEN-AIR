# managers/SNMP/snmp_utils.py
import zlib
import re
import os
from pathlib import Path

# Global map: "clean/path/prefix" -> "numerical_node_id"
_clean_to_num_map = {}

def initialize_oid_map(display_root):
    """
    Crawls the display directory to build a mapping of clean topics to sorting numbers.
    Example: 'oaGuiDefinitions/left_50/top_100' -> {'left': '50', 'left/top': '100'}
    """
    global _clean_to_num_map
    _clean_to_num_map.clear()
    
    root = Path(display_root)
    if not root.exists(): return

    for path in root.rglob("*"):
        if not path.is_dir(): continue
        
        # Build the clean path relative to display root
        rel_parts = path.relative_to(root).parts
        clean_parts = []
        num_parts = []
        
        # Trace the path to build clean vs numerical mapping
        current_clean_path = []
        temp_path = root
        for p in rel_parts:
            # Extract number
            num_match = re.search(r"(\d+)", p)
            num = num_match.group(1) if num_match else None
            
            # Extract clean name
            clean = re.sub(r"^(\d+)[_-]|[_-](\d+)$", "", p).replace(" ", "_")
            
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
    Builds a unique, non-redundant SMIv2 descriptor from a clean path.
    Name + 4-char path hash (e.g. right3a1b).
    """
    if not path_parts: return "v1"
    p = path_parts[-1]
    
    # Clean string: letters only
    clean = re.sub(r"[^a-zA-Z]", "", p)
    if not clean: clean = "node"
    
    # Ensure lowercase start for SMIv2 compliance
    base = clean[0].lower() + clean[1:]
    
    # 4-character deterministic path hash for uniqueness
    full_path = "/".join(path_parts).lower()
    h_str = hex(zlib.crc32(full_path.encode()) & 0xffffffff)[2:6].zfill(4)
    
    return f"{base}{h_str}"
