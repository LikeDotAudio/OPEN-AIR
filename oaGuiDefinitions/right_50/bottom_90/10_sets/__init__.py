# 10_sets/__init__.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Description: This file (__init__.py) marks the 'datasets' directory as a Python package and initializes its components.

Current_Date = 20251226  ##Update on the day the change was made
Current_Time = 120000  ## update at the time it was edited and compiled
Current_iteration = 44  ## a running version number - incriments by one each time

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = Current_Date * Current_Time * Current_iteration


# Author: Anthony Peter Kuzub
#
#
#

from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file


# The wrapper functions debug_log and _switch are removed
# as the core debug_log and  now directly handle LOCAL_DEBUG.
