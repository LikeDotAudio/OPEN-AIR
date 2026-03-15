# setup/path_initializer.py
#
# This module initializes global project paths, including the project root and data directory, and adds them to the system path.
# Optimized: Implements static path caching to eliminate redundant 'resolve()' and 'join()' calls.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260222.Optimized.1

import os
import sys
import pathlib

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from loguru import logger

# ⚡ CACHE: Store resolved paths as module-level constants to avoid recalculation
GLOBAL_PROJECT_ROOT = None
DATA_DIR = None

def initialize_paths():
    """
    Initializes global project paths once and returns them.
    Subsequent calls return the cached constants instantly.
    """
    global GLOBAL_PROJECT_ROOT, DATA_DIR

    # ⚡ OPTIMIZATION: Return cached values if already initialized
    if GLOBAL_PROJECT_ROOT is not None and DATA_DIR is not None:
        return GLOBAL_PROJECT_ROOT, DATA_DIR

    # --- GLOBAL PATH ANCHOR ---
    # Determine the absolute, true root path of the project.
    # Since this file is in workers/initialization/, the root is 3 levels up.
    GLOBAL_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
    
    # Add project root to sys.path if not already present
    root_str = str(GLOBAL_PROJECT_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    
    # --- Set DATA_DIR ---
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running as a bundled executable
        DATA_DIR = pathlib.Path(os.path.dirname(sys.executable)) / "DATA"
    else:
        DATA_DIR = GLOBAL_PROJECT_ROOT / "DATA"

    # Ensure directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    return GLOBAL_PROJECT_ROOT, DATA_DIR

# ⚡ AUTO-INITIALIZATION on import to provide constants immediately
initialize_paths()
