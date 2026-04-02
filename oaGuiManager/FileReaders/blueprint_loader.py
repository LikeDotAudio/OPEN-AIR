# FileReaders/blueprint_loader.py
# Author: Anthony Peter Kuzub
# Version: 20260314.120000.REV01
#
# Description: managers/Display/loader/blueprint_loader.py
"""
blueprint_loader.py - High-Performance GUI Configuration Loader.

Purpose:
    Handles the retrieval, validation, and recursive merging of GUI JSON
    blueprints. It serves as the primary data ingestion point for the
    Dynamic GUI Builder, ensuring that all UI configurations are normalized
    and merged with system-wide defaults before rendering.

Responsibilities:
    - Load JSON blueprints from disk using high-speed 'orjson' parsing.
    - Implement MD5-based hash verification to detect configuration changes
      and optimize re-renders.
    - Recursively merge specific tab configurations with the global
      'default_panel.json' to ensure consistent industrial styling.
    - Pre-normalize the entire configuration tree to "flatten" widget
      metadata, reducing overhead during the grid-rendering phase.

Constraints:
    - Expects 'default_panel.json' to exist in the parent 'managers/Display/'
      directory.
    - Uses module-level caching for the default configuration to minimize
      disk I/O on hot paths.
"""

import sys
import os

# Add the hyphenated directory to sys.path temporarily to import compiler_hook
_rs_dir = os.path.join(os.path.dirname(__file__), "oaBlueprintParser-rs")
if _rs_dir not in sys.path:
    sys.path.insert(0, _rs_dir)

import compiler_hook
compiler_hook.ensure_compiled()

try:
    import oablueprintparser_rs
except ImportError as e:
    from loguru import logger
    logger.critical("🚀❌ [FATAL] Rust Blueprint Parser module missing. Pure Rust mode is mandatory.")
    raise e

import hashlib
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import orjson
import copy
from pathlib import Path
from loguru import logger

# LOCAL_DEBUG: Toggles verbose tracing for blueprint loading and merging.

# --- Module-Level Caches ---
_DEFAULT_CONFIG_CACHE = None

class BlueprintLoader:
    """
    Orchestrates File I/O, Integrity Verification, and Configuration Merging.
    """

    @staticmethod
    def invalidate_cache():
        """
        Force-clears the cached default configuration.

        Lead with action: Flushes the '_DEFAULT_CONFIG_CACHE' global variable,
        ensuring that the next load operation retrieves the 'default_panel.json'
        directly from the filesystem.
        """
        global _DEFAULT_CONFIG_CACHE
        _DEFAULT_CONFIG_CACHE = None
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "♻️ BlueprintLoader: Global cache invalidated.", level="INFO")

    @staticmethod
    def load_blueprint(json_filepath: Path, tab_name: str, last_hash: str = None):
        """
        Retrieves and prepares a GUI blueprint for the builder.
        """
        if json_filepath is None or not json_filepath.exists():
            # Fallback to the default configuration if the specific file is 
            # missing (unless it's a temporary preview).
            if tab_name != "InteractivePreview":
                default = BlueprintLoader._load_default_config()
                normalized = BlueprintLoader._recursively_normalize(default)
                return normalized, None, True
            return {}, None, True

        # ⚡ ZERO EXCEPTION: Pre-read validation
        if json_filepath.stat().st_size == 0:
            logger.error(f"❌ BlueprintLoader: Empty file at {json_filepath}")
            return {}, None, False

        with open(json_filepath, "r") as f:
            raw_content = f.read()

        # Generate SHA256 hash for rapid change detection (Satisfies security audit).
        current_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
        if last_hash == current_hash:
            return None, current_hash, False

        # ⚡ PRE-VALIDATION: Structural integrity check
        stripped_content = raw_content.strip()
        if not stripped_content.startswith(("{", "[")) or not stripped_content.endswith(("}", "]")):
            logger.error(f"❌ BlueprintLoader: JSON structural validation failed for {json_filepath}")
            return {}, current_hash, False

        # 1. Parse the specific GUI configuration using high-speed orjson.
        specific_config = orjson.loads(raw_content)
        
        # 2. Merge with global defaults to ensure theme consistency.
        default_config = BlueprintLoader._load_default_config()
        config_data = BlueprintLoader._recursive_merge(default_config, 
                                                        specific_config)
        
        # 3. ⚡ PERFORMANCE: Pre-normalize the entire tree.
        config_data = BlueprintLoader._recursively_normalize(config_data)
        
        return config_data, current_hash, True


    @staticmethod
    def _recursively_normalize(config, root=None):
        """
        Recursively applies schema normalization to a configuration tree.

        Inputs:
            config (dict): The configuration branch to normalize.
            root (dict): The root of the entire tree (for cross-references).
        """
        from oaGuiManager.Core.parser.widget_schema_normalizer import WidgetSchemaNormalizer
        if root is None: 
            root = config
        
        if not isinstance(config, dict):
            return config
            
        # 1. Normalize the current level (flattens geometry/cosmetics).
        config = WidgetSchemaNormalizer.normalize(config, root_config=root)
        
        # 2. Optimized recursion: Only descend into logical widget containers.
        if "fields" in config:
            fields = config["fields"]
            if isinstance(fields, dict):
                for key, field in fields.items():
                    fields[key] = BlueprintLoader._recursively_normalize(field, root)
            elif isinstance(fields, list):
                for i, field in enumerate(fields):
                    fields[i] = BlueprintLoader._recursively_normalize(field, root)
        
        elif "blocks" in config:
            blocks = config["blocks"]
            if isinstance(blocks, dict):
                for key, block in blocks.items():
                    blocks[key] = BlueprintLoader._recursively_normalize(block, root)
            elif isinstance(blocks, list):
                for i, block in enumerate(blocks):
                    blocks[i] = BlueprintLoader._recursively_normalize(block, root)
        
        elif not config.get("type"):
            # If the current level has no 'type', it is a structural container.
            for key, value in config.items():
                if isinstance(value, dict):
                    # Skip known metadata keys to avoid redundant processing.
                    if key not in ["background", "styles", "style", "behavior", 
                                   "metadata", "geometry", "cosmetics", "domain", 
                                   "dynamics", "readout", "interaction", "layout"]:
                        config[key] = (
                            BlueprintLoader._recursively_normalize(value, root)
                        )
                elif isinstance(value, list) and key in ["items", "blocks", "fields"]:
                     for i, item in enumerate(value):
                         value[i] = BlueprintLoader._recursively_normalize(item, root)
                
        return config

    @staticmethod
    def _load_default_config():
        """
        Loads the system default configuration with memory-caching.
        """
        global _DEFAULT_CONFIG_CACHE
        if _DEFAULT_CONFIG_CACHE is not None:
            return copy.deepcopy(_DEFAULT_CONFIG_CACHE)

        # Locate default_panel.json relative to the current module path.
        current_dir = Path(__file__).resolve().parent
        default_path = current_dir.parent / "Constants" / "default_panel.json"
        
        if default_path.exists() and default_path.stat().st_size > 0:
            with open(default_path, "r") as f:
                raw_data = f.read()
                # ⚡ PRE-VALIDATION: Structural check
                if raw_data.strip().startswith("{"):
                    _DEFAULT_CONFIG_CACHE = orjson.loads(raw_data)
                    return copy.deepcopy(_DEFAULT_CONFIG_CACHE)
                else:
                    logger.warning(f"🟡 BlueprintLoader: default_panel.json failed structural check.")
        else:
            logger.warning(f"🟡 BlueprintLoader: default_panel.json missing or empty.")
            
        return {}


    @staticmethod
    def _recursive_merge(base, overrides):
        """
        Recursively merges an override dictionary into a base dictionary.

        Inputs:
            base (dict): The underlying configuration (typically defaults).
            overrides (dict): The specific configuration to apply on top.

        Outputs:
            dict: The combined result of the merge.
        """
        # Ensure the base is cloned to prevent accidental mutation of the cache.
        result = copy.deepcopy(base)
        for key, value in overrides.items():
            if (isinstance(value, dict) and key in result and 
                isinstance(result[key], dict)):
                result[key] = BlueprintLoader._recursive_merge(result[key], 
                                                                value)
            else:
                result[key] = copy.deepcopy(value)
        return result
