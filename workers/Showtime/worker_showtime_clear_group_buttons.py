import inspect
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config                                                                          

app_constants = Config.get_instance() # Get the singleton instance      

def clear_group_buttons(showtime_tab_instance):
    current_function = inspect.currentframe().f_code.co_name
    if showtime_tab_instance.LOCAL_DEBUG_ENABLE:
        debug_logger(
            message="🟢️️️🔵 Clearing group buttons.",
            **_get_log_args()
            


        )
    for widget in showtime_tab_instance.group_frame.winfo_children():
        widget.destroy()