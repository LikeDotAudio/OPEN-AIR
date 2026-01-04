# managers/configini/logger_config.py

import pathlib
from workers.logger.logger import  set_log_directory 

def configure_logger(data_dir, _func):
    # Configure the logger with the correct 
    set_log_directory(pathlib.Path(data_dir) / "debug")
    _func("DEBUG: Logger configured via workers.logger.logger.set_log_directory.")