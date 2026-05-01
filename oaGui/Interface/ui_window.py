# Interface/ui_window.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import inspect
import json
import os
import sys
import tkinter as tk
import traceback

from loguru import logger

from oaLogging.Methods.matrix_gate import matrix_log
from oaOchestration.Constants.project_paths import LAYOUT_CACHE_PATH

# --- Standard Debug Logging Setup ---

class UIWindowManager:
    """Handles the creation and styling configuration of the main Tkinter root window."""

    @staticmethod
    def create_root_window():
        root = tk.Tk()
        root.configure(bg="#2b2b2b")

        def _report_callback_exception(exc, value, tb):
            import traceback
            logger.error(f"🖥️🎨 [UI] CRITICAL: Tkinter Exception:\n{''.join(traceback.format_exception(exc, value, tb))}")

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

        # ⚡ V3.1.26 GEOMETRY RESTORATION:
        UIWindowManager.restore_window_geometry(root)

        # root.withdraw() # Removed as per BUG_20260404_225000.md to fix X11 BadValue error.
        return root

    @staticmethod
    def restore_window_geometry(root):
        """Loads last known window size and position from disk."""
        try:
            if os.path.exists(LAYOUT_CACHE_PATH):
                with open(LAYOUT_CACHE_PATH) as f:
                    cache = json.load(f)
                    geom = cache.get("window_geometry")
                    if geom:
                        root.geometry(geom)
                        matrix_log("UI", "GUI_MANAGER", "restore_window_geometry", f"Restored window geometry: {geom}", level="INFO")
                        return

            # Default center if no cache
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            ww, wh = 1200, 800
            x, y = (sw // 2) - (ww // 2), (sh // 2) - (wh // 2)
            root.geometry(f"{ww}x{wh}+{x}+{y}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to restore window geometry: {e}")

    @staticmethod
    def save_window_geometry(root):
        """Saves current window size and position to disk."""
        try:
            # Do not save if window is minimized or zoomed (we want normal restore)
            if root.state() != "normal":
                return

            geom = root.geometry()

            cache = {}
            if os.path.exists(LAYOUT_CACHE_PATH):
                with open(LAYOUT_CACHE_PATH) as f:
                    try: cache = json.load(f)
                    except: pass

            cache["window_geometry"] = geom

            os.makedirs(os.path.dirname(LAYOUT_CACHE_PATH), exist_ok=True)
            with open(LAYOUT_CACHE_PATH, "w") as f:
                json.dump(cache, f, indent=4)

            matrix_log("UI", "GUI_MANAGER", "save_window_geometry", f"Saved window geometry: {geom}", level="DEBUG")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save window geometry: {e}")

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
            try:
                sw, sh = max(1, root.winfo_screenwidth()), max(1, root.winfo_screenheight())
                root.geometry(f"{sw}x{sh}+0+0")
                matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"Set fallback geometry to {sw}x{sh}+0+0.", level="DEBUG")
            except tk.TclError as e:
                logger.error(f"🖥️🎨 [UI] TclError during fallback geometry setting: {e}")
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"🖥️🎨 [UI] Unexpected error during window attribute/geometry setting: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Fallback geometry as a last resort
            sw, sh = max(1, root.winfo_screenwidth()), max(1, root.winfo_screenheight())
            root.geometry(f"{sw}x{sh}+0+0")
            matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"Set fallback geometry due to unexpected error to {sw}x{sh}+0+0.", level="DEBUG")

        # ⚡ SPLASH DISMISSAL: Destroy the splash screen BEFORE revealing the main window
        # to ensure X11 display handles are correctly transferred and to avoid
        # geometry calculation conflicts.
        splash.hide()
        root.update_idletasks()

        root.deiconify()
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, "🖥️🎨 [UI] Main window deiconified.", level="DEBUG")
