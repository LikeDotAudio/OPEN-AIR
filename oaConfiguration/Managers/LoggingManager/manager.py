# oaConfiguration/Managers/LoggingManager/manager.py
#
# Centralized Manager for the Hierarchical Debug Matrix.
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
# Version 20260330.1200.1

import threading
from loguru import logger

class LoggingMatrixManager:
    """
    Orchestrates the hierarchical debug matrix for the OPEN-AIR project.

    This manager acts as the central authority for determining if a debug
    log should be emitted, based on a hierarchical tree of permissions:
    Master -> Function -> Element -> System.

    Responsibilities:
    - Core: Maintains the state of the debug matrix.
    - Core: Provides high-speed gate-keeping for log emission.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        """
        Initializes the LoggingMatrixManager.
        
        This method is called by the singleton accessor. It initializes the
        internal matrix state and loads settings from the configuration.
        """
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self._matrix = {}
        self._mute_functions = set()
        self._force_functions = set()
        self.load_from_config()

    @classmethod
    def get_instance(cls):
        """
        Retrieves the thread-safe singleton instance of the manager.

        Returns:
            LoggingMatrixManager: The global instance of the matrix manager.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def load_from_config(self, config_obj=None):
        """
        Loads or reloads the debug matrix from the system configuration.

        If no config_obj is provided, it attempts to fetch the global Config
        singleton. It populates the matrix with SYS_* and ELEMENT_* flags,
        and sets up MUTE and FORCE lists for function-level control.

        Args:
            config_obj (Config, optional): An object containing the configuration
                parameters. Defaults to None.
        
        Side Effects:
            Updates self._matrix, self._mute_functions, and self._force_functions.
        """
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
            # Sync the master killswitch with the global debug mode if not 
            # explicitly set
            if "MASTER_DEBUG_ENABLE" not in self._matrix:
                self._matrix["MASTER_DEBUG_ENABLE"] = config_obj.ENABLE_DEBUG_MODE

    def is_debug_allowed(self, system: str, element: str = None, 
                         func_name: str = None) -> bool:
        """
        Evaluates if a debug log is permitted based on the current matrix.

        This is the primary gatekeeper for logging. It evaluates rules in
        order of specificity:
        1. Master Killswitch (Global)
        2. Function Level (Mute/Force sets)
        3. Element Level (ELEMENT_ prefixed keys)
        4. System Level (SYS_ prefixed keys)

        Args:
            system (str): The subsystem name (e.g., 'CORE', 'MQTT').
            element (str, optional): The specific element within the system.
            func_name (str, optional): The name of the calling function.

        Returns:
            bool: True if logging is permitted, False otherwise.
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
        """
        Updates a specific matrix flag at runtime.

        Args:
            key (str): The matrix key to update (case-insensitive).
            value (bool): The new state for the flag.
        """
        self._matrix[key.upper()] = value

    def get_matrix(self):
        """
        Retrieves a copy of the current debug matrix.

        Returns:
            dict: A copy of the internal matrix dictionary.
        """
        return self._matrix.copy()
