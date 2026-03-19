# setup/worker_project_paths.py
#
# This module defines all application file paths relative to the project root,
# ensuring consistent file access across all sub-modules.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20250821.200641.1

import os
import inspect
import pathlib
import sys

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config
# ⚡ OPTIMIZATION: Use static path cache
from ..Core.path_initializer import (
    GLOBAL_PROJECT_ROOT, 
    DATA_RUNNING_DIR, 
    DATA_LOGS_DIR, 
    DATA_CACHE_DIR, 
    DATA_SNMP_DIR, 
    DATA_SPLINKS_DIR
)

app_constants_config = Config.get_instance()  # Get the singleton instance


# --- Global Scope Variables ---
current_version = "20251013.212800.2"
current_version_hash = 20251013 * 212800 * 2
current_file = f"{os.path.basename(__file__)}"

# --- Core Project Paths (Relative to GLOBAL_PROJECT_ROOT) ---

# ⚡ OPTIMIZATION: Resolve paths once using cached project root
MARKERS_JSON_PATH = DATA_RUNNING_DIR / "MARKERS.json"
MARKERS_CSV_PATH = DATA_RUNNING_DIR / "MARKERS.csv"
DEVICE_STATE_CACHE_PATH = DATA_CACHE_DIR / "device_state_cache.json"
LAYOUT_CACHE_PATH = DATA_CACHE_DIR / "layout_cache.json"
STATE_VISA_FLEET_JSON_PATH = DATA_RUNNING_DIR / "STATE_VISA_FLEET.json"
QUERY_DATA_DIR = DATA_CACHE_DIR / "query_data"
TABLES_DIR = DATA_CACHE_DIR / "Tables"
YAKETY_YAK_REPO_PATH = DATA_RUNNING_DIR / "YAKETYYAK.json"
PRESET_REPO_PATH = DATA_RUNNING_DIR / "PRESET.csv"

# --- SNMP Temporary & State Paths ---
SNMP_DATA_DIR = DATA_SNMP_DIR
SNMP_STATE_FILE = SNMP_DATA_DIR / "openair_snmp_objects.txt"
SNMP_SET_LOG = SNMP_DATA_DIR / "openair_snmp_set.log"
SNMP_TEMP_MIB = SNMP_DATA_DIR / "OPENAIR-MIB.txt"

# --- Persistent MIB Management ---
SNMP_MIB_DIR = SNMP_DATA_DIR / "MIB"
SNMP_CURRENT_MIB = SNMP_MIB_DIR / "current.mib"

# Ensure SNMP directories exist immediately
SNMP_DATA_DIR.mkdir(parents=True, exist_ok=True)
SNMP_MIB_DIR.mkdir(parents=True, exist_ok=True)


def get_absolute_path(relative_path: str):
    """
    Utility function to return an absolute path for a string relative to the project root.
    """
    try:
        # Use simple joining with the cached root
        return GLOBAL_PROJECT_ROOT / relative_path
    except Exception as e:
        print(f"❌ Error resolving path: {e}")
        return pathlib.Path(relative_path)  # Return a relative path as a fallback
