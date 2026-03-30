# oaConfiguration/Managers/LoggingManager/manager.py
# Author: Anthony Peter Kuzub
# Version: 20260329.2345.1
#
# Description: Centralized Manager for the Hierarchical Debug Matrix.
# Maps config.ini [DEBUG_MATRIX] settings to runtime logic for surgical logging.

import threading
from loguru import logger

class LoggingMatrixManager:
    """
    Orchestrates the hierarchical debug matrix for the OPEN-AIR project.
    Allows for system, element, and function level logging control.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self._matrix = {}
        self._mute_functions = set()
        self._force_functions = set()
        self.load_from_config()

    @classmethod
    def get_instance(cls):
        """Thread-safe singleton accessor."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def load_from_config(self, config_obj=None):
        """Loads or reloads the matrix from the central config file."""
        if config_obj is None:
            try:
                from oaConfiguration.FileReaders.config_reader import Config
                config_obj = Config.get_instance()
            except Exception:
                pass
        
        # ⚡ ROBUSTNESS: Use defaults if config system is not yet ready
        self._matrix = getattr(config_obj, "DEBUG_MATRIX", {
            "MASTER_DEBUG_ENABLE": True,
            "SYS_CORE": True
        }).copy()
        
        m_funcs = getattr(config_obj, "MUTE_FUNCTIONS", "")
        f_funcs = getattr(config_obj, "FORCE_FUNCTIONS", "")
        
        self._mute_functions = {f.strip() for f in m_funcs.split(",") if f.strip()}
        self._force_functions = {f.strip() for f in f_funcs.split(",") if f.strip()}
        
        if config_obj and hasattr(config_obj, "ENABLE_DEBUG_MODE"):
            # Sync the master killswitch with the global debug mode if not explicitly set
            if "MASTER_DEBUG_ENABLE" not in self._matrix:
                self._matrix["MASTER_DEBUG_ENABLE"] = config_obj.ENABLE_DEBUG_MODE

    def is_debug_allowed(self, system: str, element: str = None, func_name: str = None) -> bool:
        """
        The Pre-Gate check. High speed evaluation of matrix rules.
        """
        # 1. Master Killswitch
        if not self._matrix.get("MASTER_DEBUG_ENABLE", True):
            return False

        # 2. Function Level (Highest Precision)
        if func_name:
            if func_name in self._mute_functions:
                return False
            if func_name in self._force_functions:
                return True

        # 3. Element Level Override (Medium Precision)
        if element:
            el_key = f"ELEMENT_{element.upper()}"
            if el_key in self._matrix:
                return self._matrix[el_key]

        # 4. System Level (Macro Precision)
        sys_key = f"SYS_{system.upper()}"
        return self._matrix.get(sys_key, False)

    def update_matrix(self, key: str, value: bool):
        """Updates a matrix value at runtime."""
        self._matrix[key.upper()] = value
        # In a real scenario, we might want to write back to config.ini here.

    def get_matrix(self):
        """Returns the current state of the debug matrix."""
        return self._matrix.copy()
