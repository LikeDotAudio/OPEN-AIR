# Constants/project_paths.py
#
# Defines all application file paths relative to the project root.
# Provides a centralized repository for path management and directory creation.
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
# Version 20260330.1600.1

import os
import inspect
import pathlib
import sys
from loguru import logger

# --- Standard Debug Logging Setup ---
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
        logger.error(f"❌ Error resolving path: {e}")
        return pathlib.Path(relative_path)  # Return a relative path as a fallback
