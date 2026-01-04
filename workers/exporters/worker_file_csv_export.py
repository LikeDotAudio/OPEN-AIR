# workers/worker_file_csv_export.py
#
# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# As the current hour is 20, no change is needed.

Current_Date = 20251129  ##Update on the day the change was made
Current_Time = 120000  ## update at the time it was edited and compiled
Current_iteration = 1 ## a running version number - incriments by one each time 

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = (Current_Date * Current_Time * Current_iteration)


# A utility module to handle the logic for exporting data to a CSV file.
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
#
# Version 20250824.120616.1

import csv
import inspect
import os

from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args 
from managers.configini.config_reader import Config                                                                          

app_constants = Config.get_instance() # Get the singleton instance      

# --- Global Scope Variables ---
CURRENT_DATE = 20250824
CURRENT_TIME = 120616
CURRENT_TIME_HASH = 120616
REVISION_NUMBER = 1
current_version = f"{CURRENT_DATE}.{CURRENT_TIME}.{REVISION_NUMBER}"
current_version_hash = (int(CURRENT_DATE) * CURRENT_TIME_HASH * REVISION_NUMBER)
current_file = f"{os.path.basename(__file__)}"
LOCAL_DEBUG_ENABLE = False


class CsvExportUtility:
    """
    A utility class to handle CSV file export logic.
    """
    def __init__(self, print_to_gui_func):
        self._print_to_gui_console = print_to_gui_func

    def export_data_to_csv(self, data, file_path):
        """
        Exports a list of dictionaries to a CSV file.
        
        Args:
            data (list of dict): The data to export. Each dictionary represents a row.
            file_path (str): The path to the output CSV file.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🟢️️️🟢 ➡️➡️ '{current_function_name}' to save data to CSV at '{file_path}'.",
              **_get_log_args()
                
            )
        
        try:
            if not data:
                debug_logger(message="❌ No data to export.")
                return

            # Grab the headers from the first dictionary's keys
            headers = data[0].keys()
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
                
            debug_logger(message=f"✅ Data successfully exported to {file_path}")
            
        except Exception as e:
            debug_logger(message=f"❌ Error in {current_function_name}: {e}")
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"❌🔴 Arrr, the code be capsized! The error be: {e}",
**_get_log_args()
                    
                )