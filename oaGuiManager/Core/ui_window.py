# Core/ui_window.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import sys
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import tkinter as tk
import traceback
from loguru import logger

# --- Standard Debug Logging Setup ---

class UIWindowManager:
    """Handles the creation and styling configuration of the main Tkinter root window."""

    @staticmethod
    def create_root_window():
        root = tk.Tk()
        root.configure(bg="#2b2b2b")
        
        def _report_callback_exception(exc, val, tb):
            import traceback
            logger.error(f"🖥️🎨 [UI] CRITICAL: Tkinter Exception:\n{''.join(traceback.format_exception(exc, val, tb))}")
        
        root.report_callback_exception = _report_callback_exception
        
        # Establish Global Style Defaults
        root.option_add("*Background", "#2b2b2b")
        root.option_add("*Foreground", "#dcdcdc")
        root.option_add("*Entry.background", "#3c3f41")
        root.option_add("*Entry.foreground", "#ffffff")
        root.option_add("*Text.background", "#1e1e1e")
        root.option_add("*Text.foreground", "#dcdcdc")
        
        root.title("OPEN-AIR (Partitioned UI)")
        
        # ⚡ ENFORCE MINIMUM SIZE: Prevent the window from collapsing (e.g., when moving between screens)
        WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT = 800, 600
        root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"Enforced minimum window size: {WINDOW_MIN_WIDTH}x{WINDOW_MIN_HEIGHT}", level="DEBUG")
    
        root.withdraw()
        return root

    @staticmethod
    def reveal_main_window(root, splash, debug_enabled):
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "🖥️🎨 [UI] Reveal main window.", level="DEBUG")
        
        # Apply OS-specific window maximization logic and handle errors gracefully
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "Attempting to set window maximization attributes...", level="DEBUG")
        try:
            if sys.platform.startswith("linux"):
                root.attributes("-zoomed", True)
                matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "Set '-zoomed' attribute for Linux.", level="DEBUG")
            else:
                root.state("zoomed")
                matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "Set 'zoomed' state for non-Linux.", level="DEBUG")
        
            # Ensure window is updated after setting state/attributes
            root.update_idletasks()

        except tk.TclError as e:
            # Log TclErrors specifically related to window attributes/geometry
            logger.error(f"🖥️🎨 [UI] TclError during window maximization/state setting: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Fallback to setting geometry if maximization fails
            matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "Maximization failed. Falling back to setting window geometry...", level="DEBUG")
            sw, sh = max(1, root.winfo_screenwidth()), max(1, root.winfo_screenheight())
            root.geometry(f"{sw}x{sh}+0+0")
            matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"Set fallback geometry to {sw}x{sh}+0+0.", level="DEBUG")
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"🖥️🎨 [UI] Unexpected error during window attribute/geometry setting: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Fallback geometry as a last resort
            sw, sh = max(1, root.winfo_screenwidth()), max(1, root.winfo_screenheight())
            root.geometry(f"{sw}x{sh}+0+0")
            matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"Set fallback geometry due to unexpected error to {sw}x{sh}+0+0.", level="DEBUG")

        root.deiconify()
        splash.hide()
