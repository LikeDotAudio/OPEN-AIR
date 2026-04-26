# oaGuiEditorWYSIWYG/Managers/runner/runner_env.py
# Author: Anthony Peter Kuzub
# Version: 20260416.0230.1
#
# Description: Environment bootstrapper for the Standalone WYSIWYG Editor.

import pathlib
import sys

from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Core.logger import initialize_logging, set_log_directory
from oaOchestration.Core.path_initializer import DATA_LOGS_DIR, initialize_paths


class RunnerEnvironment:
    """Manages the standalone environment setup (Paths, Logging, sys.path)."""

    @staticmethod
    def setup():
        """
        Initializes the project environment for a standalone process.
        Ensures all OPEN-AIR infrastructure is ready before UI launch.
        """
        # 1. Setup global path context and create missing oaData* folders
        initialize_paths()

        # 2. Add Project Root to sys.path to resolve absolute imports
        project_root = pathlib.Path(__file__).resolve().parent.parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        # 3. Initialize Logging and configuration
        config = Config.get_instance()
        set_log_directory(DATA_LOGS_DIR, partition="WYSIWYG")
        initialize_logging(config, log_dir=DATA_LOGS_DIR, partition="WYSIWYG")

        return config
