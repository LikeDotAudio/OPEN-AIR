# workers/wysiwyg_editor/grab_bag/grab_bag_loader.py
#
# Scans the builder directories for sample.json files to populate the Grab Bag palette.
#
# Author: Gemini CLI

import orjson
import os
from pathlib import Path
from oaLogging.logger import initialize_logging, set_log_directory
from loguru import logger

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file


class GrabBagLoader:
    """Discovers and loads modular UI components from the builder library."""

    def __init__(self, builder_root="workers/builder"):
        self.builder_root = Path(builder_root)
        self.library = {}
        if LOCAL_DEBUG: logger.debug(f"🎒 GrabBagLoader: Initialized. Scanning root: {builder_root}")

    def scan_library(self):
        """Crawls the builder directory for folders containing sample.json."""
        self.library = {}
        if not self.builder_root.exists():
            logger.error(f"❌ GrabBagLoader: Builder root '{self.builder_root}' does not exist.")
            return self.library

        if LOCAL_DEBUG: logger.info("🎒 GrabBagLoader: Starting library scan...")
        
        for item in self.builder_root.iterdir():
            if item.is_dir():
                sample_file = item / "sample.json"
                if sample_file.exists():
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
                        logger.exception("❌ GrabBagLoader: Error loading sample from {item.name}")
        
        if LOCAL_DEBUG: logger.success(f"✅ GrabBagLoader: Scan complete. Found {len(self.library)} valid components.")
        return self.library

    def get_component(self, name):
        """Returns the schema and metadata for a specific component."""
        return self.library.get(name)
