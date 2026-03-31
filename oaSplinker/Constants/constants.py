# Constants/constants.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import threading
import time
import orjson
import os
from pathlib import Path
from loguru import logger
from oaConfiguration.FileReaders.config_reader import Config
from oaOchestration.Core.path_initializer import DATA_SPLINKS_DIR

Splinker_debug_enabled = False
app_constants = Config.get_instance()
splinker_logger = logger.bind(subsystem="SPLINKER", category="COMM")

# --- Handler Imports ---
from ..Methods.debounce_handler import DebounceHandler
from ..Methods.deadband_handler import DeadbandHandler
from ..Methods.scale_handler import ScaleHandler
from ..Methods.invert_handler import InvertHandler

# --- Storage ---
SPLINKER_STORAGE_PATH = DATA_SPLINKS_DIR

# --- Handler Mapping ---
HANDLER_MAP = {
    "debounce": DebounceHandler,
    "deadband": DeadbandHandler,
    "scale": ScaleHandler,
    "invert": InvertHandler,
}
