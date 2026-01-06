import inspect
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.Showtime.worker_showtime_tune import on_tune_request_from_selection


def on_marker_button_click(showtime_tab_instance, button):
    current_function = inspect.currentframe().f_code.co_name
    if showtime_tab_instance.LOCAL_DEBUG_ENABLE:
        debug_logger(
            message="🟢️️️🔵 Device button clicked. Toggling selection.", **_get_log_args()
        )
    marker_data = button.marker_data

    if showtime_tab_instance.selected_device_button == button:
        showtime_tab_instance.selected_device_button.config(style="Custom.TButton")
        showtime_tab_instance.selected_device_button = None
        debug_logger(
            message=f"🟡 Deselected device: {marker_data.get('NAME', 'N/A')}.",
            **_get_log_args(),
        )
    else:
        if showtime_tab_instance.selected_device_button:
            showtime_tab_instance.selected_device_button.config(style="Custom.TButton")

        showtime_tab_instance.selected_device_button = button
        showtime_tab_instance.selected_device_button.config(
            style="Custom.Selected.TButton"
        )
        debug_logger(
            message=f"✅ Selected device: {marker_data.get('NAME', 'N/A')} at {marker_data.get('FREQ_MHZ', 'N/A')} MHz.",
            **_get_log_args(),
        )

    on_tune_request_from_selection(showtime_tab_instance)
