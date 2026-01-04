# workers.setup.path_initializer.py

import os
import sys
import pathlib
from managers.configini.config_reader import Config
app_constants = Config.get_instance() # Get the singleton instance
from workers.logger.logger import  debug_logger # import  debug_logger
from workers.logger.log_utils import _get_log_args # Import _get_log_args

GLOBAL_PROJECT_ROOT = None
DATA_DIR = None

def initialize_paths(): # Removed _func argument
    global GLOBAL_PROJECT_ROOT, DATA_DIR

    # --- GLOBAL PATH ANCHOR (CRITICAL FIX: Ensure this runs first!) ---
    # This defines the absolute, true root path of the project, irrespective of the CWD.
    GLOBAL_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent # Adjust path for setup directory
    debug_logger(message=f"📁 GLOBAL_PROJECT_ROOT set to {GLOBAL_PROJECT_ROOT}", **_get_log_args())
    # Add the project's root directory to the system path to allow for imports from
    # all sub-folders (e.g., 'configuration' and 'display'). This is a robust way to handle imports.
    if str(GLOBAL_PROJECT_ROOT) not in sys.path:
        sys.path.append(str(GLOBAL_PROJECT_ROOT))
    debug_logger(message=f"⚙️ sys.path updated. Current sys.path: {sys.path}", **_get_log_args())


    # --- Set DATA_DIR ---
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as a bundled executable
        DATA_DIR = os.path.join(os.path.dirname(sys.executable), 'DATA')
    else:
        DATA_DIR = os.path.join(GLOBAL_PROJECT_ROOT, 'DATA')
    
    return GLOBAL_PROJECT_ROOT, DATA_DIR