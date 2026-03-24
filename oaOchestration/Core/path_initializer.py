# Core/path_initializer.py
# Author: Anthony Peter Kuzub
# Version: 20260222.Optimized.1
#
# Description: This module initializes global project paths, including the project root and data directory, and adds them to the system path.

import os
import sys
import pathlib

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from loguru import logger

# ⚡ CACHE: Store resolved paths as module-level constants to avoid recalculation
GLOBAL_PROJECT_ROOT = None
DATA_RUNNING_DIR = None
DATA_LOGS_DIR = None
DATA_CACHE_DIR = None
DATA_SNMP_DIR = None
DATA_SPLINKS_DIR = None
DATA_REPORTS_DIR = None

def initialize_paths():
    """
    Initializes global project paths once and returns them.
    Subsequent calls return the cached constants instantly.
    """
    global GLOBAL_PROJECT_ROOT, DATA_RUNNING_DIR, DATA_LOGS_DIR, DATA_CACHE_DIR, DATA_SNMP_DIR, DATA_SPLINKS_DIR, DATA_REPORTS_DIR

    # ⚡ OPTIMIZATION: Return cached values if already initialized
    if GLOBAL_PROJECT_ROOT is not None and DATA_RUNNING_DIR is not None:
        return GLOBAL_PROJECT_ROOT, DATA_RUNNING_DIR

    # --- GLOBAL PATH ANCHOR ---
    # Determine the absolute, true root path of the project.
    # Since this file is in oaOchestration/Core/, the root is 3 levels up.
    GLOBAL_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

    # Add project root to sys.path if not already present
    root_str = str(GLOBAL_PROJECT_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, str(root_str))

    # --- Set Data Directories (Consumable & Refactored Structure) ---
    # Running state is now ephemeral and stored in a hidden cache directory.
    DATA_RUNNING_DIR = GLOBAL_PROJECT_ROOT / ".pytest_cache" / "oaDataState"
    DATA_LOGS_DIR = GLOBAL_PROJECT_ROOT / "oaDataLogs"
    DATA_CACHE_DIR = GLOBAL_PROJECT_ROOT / "oaDataCache"
    DATA_SNMP_DIR = GLOBAL_PROJECT_ROOT / "oaDataSNMP"
    DATA_SPLINKS_DIR = GLOBAL_PROJECT_ROOT / "oaDataSplinks"
    DATA_REPORTS_DIR = GLOBAL_PROJECT_ROOT / "oaReports"

    # Ensure directories exist (Auto-generation)
    DATA_RUNNING_DIR.mkdir(parents=True, exist_ok=True)
    DATA_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_SNMP_DIR.mkdir(parents=True, exist_ok=True)
    DATA_SPLINKS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    return GLOBAL_PROJECT_ROOT, DATA_RUNNING_DIR


# ⚡ AUTO-INITIALIZATION on import to provide constants immediately
initialize_paths()
