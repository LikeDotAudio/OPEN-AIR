# oaGui/FileReaders/json_blueprint_reader.py
# Author: Anthony Peter Kuzub
# Version: 20260314.120000.REV01
#
# Description: managers/Display/loader/json_blueprint_reader.py

import copy
import hashlib
import inspect
from pathlib import Path

import orjson
from loguru import logger

from oaGui.Managers.persistence.cache_blueprint_store import CacheBlueprintStore
from oaGui.Methods.processing.blueprint_merger import BlueprintMerger
from oaGui.Methods.validation.json_schema_normalizer import JsonSchemaNormalizer
from oaLogging.Methods.matrix_gate import matrix_log


class JsonBlueprintReader:
    """
    Orchestrates File I/O, Integrity Verification, and Configuration Merging.
    """

    @staticmethod
    def invalidate_cache():
        """
        Force-clears the cached default configuration.
        """
        CacheBlueprintStore.invalidate()
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "♻️ JsonBlueprintReader: Global cache invalidated.", level="INFO")

    @staticmethod
    def load_blueprint(json_filepath: Path, tab_name: str, last_hash: str = None):
        """
        Retrieves and prepares a GUI blueprint for the builder.
        """
        if json_filepath is None or not json_filepath.exists():
            # Fallback to the default configuration if the specific file is
            # missing (unless it's a temporary preview).
            if tab_name != "InteractivePreview":
                default = JsonBlueprintReader._load_default_config()
                normalized = JsonSchemaNormalizer.normalize(default)
                return normalized, None, True
            return {}, None, True

        # ⚡ ZERO EXCEPTION: Pre-read validation
        if json_filepath.stat().st_size == 0:
            logger.error(f"❌ JsonBlueprintReader: Empty file at {json_filepath}")
            return {}, None, False

        with open(json_filepath) as f:
            raw_content = f.read()

        # Generate SHA256 hash for rapid change detection (Satisfies security audit).
        current_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
        if last_hash == current_hash:
            return None, current_hash, False

        # ⚡ PRE-VALIDATION: Structural integrity check
        stripped_content = raw_content.strip()
        if not stripped_content.startswith(("{", "[")) or not stripped_content.endswith(("}", "]")):
            logger.error(f"❌ JsonBlueprintReader: JSON structural validation failed for {json_filepath}")
            return {}, current_hash, False

        # 1. Parse the specific GUI configuration using high-speed orjson.
        specific_config = orjson.loads(raw_content)

        # 2. Merge with global defaults to ensure theme consistency.
        default_config = JsonBlueprintReader._load_default_config()
        configuration = BlueprintMerger.merge(default_config, specific_config)

        # 3. ⚡ PERFORMANCE: Pre-normalize the entire tree.
        configuration = JsonSchemaNormalizer.normalize(configuration)

        return configuration, current_hash, True

    @staticmethod
    def _load_default_config():
        """
        Loads the system default configuration with memory-caching.
        """
        cached = CacheBlueprintStore.get_cached_default()
        if cached is not None:
            return cached

        # Locate default_panel.json relative to the current module path.
        # current_dir is .../oaGui/FileReaders/loader
        current_dir = Path(__file__).resolve().parent
        default_path = current_dir.parent.parent / "Constants" / "default_panel.json"

        if default_path.exists() and default_path.stat().st_size > 0:
            with open(default_path) as f:
                raw_data = f.read()
                # ⚡ PRE-VALIDATION: Structural check
                if raw_data.strip().startswith("{"):
                    config = orjson.loads(raw_data)
                    CacheBlueprintStore.set_cached_default(config)
                    return copy.deepcopy(config)
                else:
                    logger.warning(f"🟡 JsonBlueprintReader: structural check failed for {default_path}")
        else:
            logger.warning(f"🟡 JsonBlueprintReader: file missing or empty at {default_path}")

        return {}
