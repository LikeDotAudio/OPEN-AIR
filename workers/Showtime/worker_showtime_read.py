# workers/Showtime/worker_showtime_read.py
#
# A complete and comprehensive pre-amble that describes the file and the functions within.
# The purpose is to provide clear documentation and versioning.
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

import inspect
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args
from workers.importers.worker_marker_file_import_handling import maker_file_check_for_markers_file
from managers.configini.config_reader import Config
app_constants = Config.get_instance() # Get the singleton instance


def load_marker_data(showtime_tab_instance):
    current_function = inspect.currentframe().f_code.co_name
    if app_constants.global_settings['debug_enabled']:
        debug_logger(
            message="🟢️️️🟢 Loading raw marker data from file.",
            **_get_log_args()
            


        )
    
    raw_headers, raw_data = maker_file_check_for_markers_file()
    
    if not raw_data:
        showtime_tab_instance.marker_data = []
        showtime_tab_instance.column_headers = []
        debug_logger(message="🟡 No marker data found in MARKERS.csv. No buttons will be created.", **_get_log_args())
        return

    showtime_tab_instance.marker_data = [dict(zip(raw_headers, row)) for row in raw_data if len(row) == len(raw_headers)]
    showtime_tab_instance.column_headers = raw_headers

    if app_constants.global_settings['debug_enabled']:
        debug_logger(
            message=f"✅ Loaded {len(showtime_tab_instance.marker_data)} rows. Converted to dictionaries for sorting and display.",
            **_get_log_args()
            


        )