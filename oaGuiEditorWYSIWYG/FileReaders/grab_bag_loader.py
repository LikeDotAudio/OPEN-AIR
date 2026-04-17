# FileReaders/grab_bag_loader.py
# Author: Gemini CLI
# Version: 1.0.1
#
# Description: Scans the builder directories for sample.json files to populate the Grab Bag palette.

import orjson
import os
import inspect
from pathlib import Path
from oaLogging.Core.logger import WYSIWYG_LOGGER
from oaLogging.Methods.matrix_gate import matrix_log

logger = WYSIWYG_LOGGER.bind(protocol="WYSIWYG")

class GrabBagLoader:
    """Discovers and loads modular UI components from the builder library."""
    _global_library_cache = None

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
        matrix_log(
            system="ui", 
            element="grab_bag", 
            func_name=inspect.currentframe().f_code.co_name,
            message=f"📦🔬🔍 [PACKAGE] GrabBagLoader: Initialized. Scanning root: {self.builder_root}",
            level="DEBUG"
        )

    def scan_library(self):
        """Crawls the builder directory for folders containing sample.json."""
        self.library = {}
        
        # ⚡ ROBUSTNESS: If the root is a standard folder but doesn't exist, log and exit
        if not self.builder_root.exists():
            logger.error(f"❌📦🤦‍♂️ [PACKAGE] GrabBagLoader: Builder root '{self.builder_root}' does not exist.")
            return self.library

        matrix_log(
            system="ui", 
            element="grab_bag", 
            func_name=inspect.currentframe().f_code.co_name,
            message=f"📦🔬🔍 [PACKAGE] GrabBagLoader: Starting library scan in {self.builder_root}...",
            level="INFO"
        )
        
        # We need to scan recursively since oaGuiElements has subfolders (Core/utils, etc.)
        for sample_file in self.builder_root.rglob("sample.json"):
            item = sample_file.parent
            if item.name == "Assets":
                item = item.parent
            
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
                        continue # Silently skip metadata-only entries in scan

                    # Use directory name as component name (e.g., 'builder_knob' -> 'knob')
                    name = item.name.replace("builder_", "").replace("_", " ").title()
                    
                    # ⚡ CATEGORIZATION: Use the parent folder name as the category
                    category = item.parent.name.replace("builder_", "").replace("_", " ").title()
                    if category == "Core": category = "General" # Flatten Core to General
                    
                    self.library[name] = {
                        "folder": item.name,
                        "full_path": str(item),
                        "schema": widget_config,
                        "type": widget_type,
                        "category": category
                    }
                    matrix_log(
                        system="ui", 
                        element="grab_bag", 
                        func_name=inspect.currentframe().f_code.co_name,
                        message=f"📦🆗✅ [PACKAGE]   ↳ Found Component: '{name}' (Type: {widget_type})",
                        level="DEBUG"
                    )
            except Exception as e:
                logger.exception(f"❌📦🤦‍♂️ [PACKAGE] GrabBagLoader: Error loading sample from {item.name}: {e}")
        
        matrix_log(
            system="ui", 
            element="grab_bag", 
            func_name=inspect.currentframe().f_code.co_name,
            message=f"📦🏁🏁 [PACKAGE] GrabBagLoader: Scan complete. Found {len(self.library)} valid components.",
            level="SUCCESS"
        )
        return self.library

    def get_component(self, name):
        """Returns the schema and metadata for a specific component."""
        return self.library.get(name)
