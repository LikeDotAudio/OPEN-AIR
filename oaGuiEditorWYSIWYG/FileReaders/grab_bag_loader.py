# FileReaders/grab_bag_loader.py
# Author: Gemini CLI
# Version: 1.0.1
#
# Description: Scans the builder directories for sample.json files to populate the Grab Bag palette.

import orjson
import os
from pathlib import Path
from oaLogging.Core.logger import WYSIWYG_LOGGER
logger = WYSIWYG_LOGGER.bind(protocol="WYSIWYG")

LOCAL_DEBUG = False    # Set to False in production, True for dev on this file


class GrabBagLoader:
    """Discovers and loads modular UI components from the builder library."""

    def __init__(self, builder_root=None):
        # ⚡ AUTONOMY: Resolve project-standard path if not provided
        if builder_root is None:
            try:
                from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
                builder_root = GLOBAL_PROJECT_ROOT / "oaGuiElements"
            except ImportError:
                # Fallback for standalone tests
                builder_root = Path("oaGuiElements")
            
        self.builder_root = Path(builder_root)
        self.library = {}
        if LOCAL_DEBUG: logger.debug(f"🎒 GrabBagLoader: Initialized. Scanning root: {self.builder_root}")

    def scan_library(self):
        """Crawls the builder directory for folders containing sample.json."""
        self.library = {}
        
        # ⚡ ROBUSTNESS: If the root is a standard folder but doesn't exist, log and exit
        if not self.builder_root.exists():
            logger.error(f"❌ GrabBagLoader: Builder root '{self.builder_root}' does not exist.")
            return self.library

        if LOCAL_DEBUG: logger.info(f"🎒 GrabBagLoader: Starting library scan in {self.builder_root}...")
        
        # We need to scan recursively since oaGuiElements has subfolders (Core/utils, etc.)
        for sample_file in self.builder_root.rglob("sample.json"):
            item = sample_file.parent
            try:
                with open(sample_file, 'r') as f:
                    sample_data = orjson.loads(f.read())
                    
                    # ⚡ SMART SCHEMA EXTRACTION: Find the actual widget config in exhaustive samples
                    widget_config = {}
                    widget_type = None
                    
                    if "type" in sample_data or "widget_type" in sample_data:
                        # Simple sample (single object)
                        widget_config = sample_data
                        widget_type = sample_data.get("type") or sample_data.get("widget_type")
                    else:
                        # Exhaustive sample (multiple keys)
                        # Find the first key that has a 'type' field and isn't a private key
                        for k, v in sample_data.items():
                            if isinstance(v, dict) and ("type" in v or "widget_type" in v):
                                widget_config = v
                                widget_type = v.get("type") or v.get("widget_type")
                                break
                    
                    if not widget_type:
                        if LOCAL_DEBUG: logger.warning(f"  ⚠️ Skipping {item.name}: No valid widget type found in sample.")
                        continue

                    # Use directory name as component name (e.g., 'builder_knob' -> 'knob')
                    name = item.name.replace("builder_", "").replace("_", " ").title()
                    self.library[name] = {
                        "folder": item.name,
                        "schema": widget_config,
                        "type": widget_type
                    }
                    if LOCAL_DEBUG: logger.debug(f"  ↳ Found Component: '{name}' (Type: {widget_type})")
            except Exception as e:
                logger.exception(f"❌ GrabBagLoader: Error loading sample from {item.name}")
        
        if LOCAL_DEBUG: logger.success(f"✅ GrabBagLoader: Scan complete. Found {len(self.library)} valid components.")
        return self.library

    def get_component(self, name):
        """Returns the schema and metadata for a specific component."""
        return self.library.get(name)
