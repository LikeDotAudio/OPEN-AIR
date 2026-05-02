# oaGui/FileReaders/scanner/layout_info_service.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for retrieving and caching layout information from directories.

import pathlib

def retrieve_cached_layout_info(scanner, path: pathlib.Path):
    """
    Retrieves layout information for a given path, using a cache to avoid redundant parsing.
    Checks directory timestamp for optimized cache invalidation.
    """
    path_str = str(path)

    try:
        current_mtime = path.stat().st_mtime
    except OSError:
        current_mtime = 0

    if hasattr(scanner, '_layout_cache') and path_str in scanner._layout_cache:
        cached_entry = scanner._layout_cache[path_str]
        if cached_entry.get("mtime") == current_mtime:
            return cached_entry

    layout_info = scanner.layout_parser.parse_directory(path)
    layout_info["mtime"] = current_mtime
    
    if hasattr(scanner, '_layout_cache'):
        scanner._layout_cache[path_str] = layout_info
        
    return layout_info
