# display/base_gui_component.py
#
# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# As the current hour is 20, no change is needed.

Current_Date = 20251129  ##Update on the day the change was made
Current_Time = 120000  ## update at the time it was edited and compiled
Current_iteration = 1 ## a running version number - incriments by one each time 

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = (Current_Date * Current_Time * Current_iteration)


# This component allows for real-time control and monitoring of MQTT messages,
# offering a centralized "conductor" view of the system's communication.
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
# Version 20251127.000000.1

import os
import inspect
import datetime
import tkinter as tk
from tkinter import ttk
import pathlib
import orjson
from collections import defaultdict

# --- Module Imports ---
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args 
from workers.styling.style import THEMES, DEFAULT_THEME

# --- Global Scope Variables ---
CURRENT_DATE = 20251127
CURRENT_TIME = 0
CURRENT_TIME_HASH = 0
REVISION_NUMBER = 1
current_version = f"{CURRENT_DATE}.{CURRENT_TIME}.{REVISION_NUMBER}"
current_version_hash = (int(CURRENT_DATE) * CURRENT_TIME_HASH * REVISION_NUMBER)
current_file = f"display/right_40/bottom_90/tab_4_conductor/{os.path.basename(__file__)}"

# --- Constant Variables (No Magic Numbers) ---
SERVER_STATUS_FRAME_TEXT = "Server Status"
PUBLISH_FRAME_TEXT = "Publish Message"
SUBSCRIPTIONS_FRAME_TEXT = "Live Subscriptions"
CLIENTS_FRAME_TEXT = "Connected Clients"
TOPIC_LABEL_TEXT = "Topic:"
SUBTOPIC_LABEL_TEXT = "Subtopic:"
VALUE_LABEL_TEXT = "Value:"
PUBLISH_BUTTON_TEXT = "Publish"
CLEAR_BUTTON_TEXT = "Clear Log"
COLUMNS = ("Topic", "Message")
SERVER_STATUS_TEXT = "Status:"
SERVER_ADDRESS_TEXT = "Broker Address:"
SERVER_VERSION_TEXT = "Version:"
SERVER_UPTIME_TEXT = "Uptime:"
SERVER_MESSAGE_COUNT_TEXT = "Messages:"
CLIENT_COUNT_TEXT = "Clients:"
FILTER_LABEL_TEXT = "Filter Topics:"
STATUS_RUNNING_TEXT = "Running"
STATUS_STOPPED_TEXT = "Stopped"


class MqttConductorFrame(ttk.Frame):
    """
    A comprehensive GUI frame for controlling and monitoring a local MQTT broker.
    It provides a centralized view of broker status, topic activity, and connected clients.
    """
    def __init__(self, parent, *args, **kwargs):
        """
        Initializes the GUI, setting up layout and widgets.
        This version integrates with the main application's MqttControllerUtility.

        Args:
            parent: The parent widget for this frame.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        
        debug_logger(
            message=f"🐐🟢 Initializing the '{self.__class__.__name__}' GUI frame. This one's a masterpiece of form over function!",
**_get_log_args()
            


        )
        
        try:
            if 'config' in kwargs:
                kwargs.pop('config')
            super().__init__(parent, **kwargs)
            
            self._apply_styles(theme_name=DEFAULT_THEME)

        except Exception as e:
            debug_logger(message=f"❌ Error in {current_function_name}: {e}")
            debug_logger(
                message=f"❌🔴 Arrr, the code be capsized! The error be: {e}",
              **_get_log_args()
                


            )

    def _apply_styles(self, theme_name: str):
        """Applies the specified theme to the GUI elements."""
        colors = THEMES.get(theme_name, THEMES["dark"])
        style = ttk.Style(self)
        style.theme_use("clam")
        
        style.configure('TFrame', background=colors["bg"])
        style.configure('TLabel', background=colors["bg"], foreground=colors["fg"])
        style.configure('TLabelframe', background=colors["bg"], foreground=colors["fg"])
        style.configure('Custom.Treeview',
                         background=colors["table_bg"],
                         foreground=colors["table_fg"],
                         fieldbackground=colors["table_bg"],
                         bordercolor=colors["table_border"],
                         borderwidth=colors["border_width"])
        style.configure('Custom.Treeview.Heading',
                         background=colors["table_heading_bg"],
                         foreground=colors["fg"],
                         relief=colors["relief"],
                         borderwidth=colors["border_width"])
        style.configure('Custom.TEntry',
                         fieldbackground=colors["entry_bg"],
                         foreground=colors["entry_fg"],
                         bordercolor=colors["table_border"])
        style.configure('TButton', background=colors["accent"], foreground=colors["text"], padding=5)