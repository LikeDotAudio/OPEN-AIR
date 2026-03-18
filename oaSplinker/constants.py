import threading
import time
import orjson
import os
from pathlib import Path
from loguru import logger
from oaConfiguration.config_reader import Config
from oaOchestration.path_initializer import DATA_SPLINKS_DIR

# --- Handler Imports ---
from .handlers.debounce_handler import DebounceHandler
from .handlers.deadband_handler import DeadbandHandler
from .handlers.scale_handler import ScaleHandler
from .handlers.invert_handler import InvertHandler

Splinker_debug_enabled = False
app_constants = Config.get_instance()
splinker_logger = logger.bind(subsystem="SPLINKER", category="COMM")

# --- Storage ---
SPLINKER_STORAGE_PATH = DATA_SPLINKS_DIR

# --- Handler Mapping ---
HANDLER_MAP = {
    "debounce": DebounceHandler,
    "deadband": DeadbandHandler,
    "scale": ScaleHandler,
    "invert": InvertHandler,
}
