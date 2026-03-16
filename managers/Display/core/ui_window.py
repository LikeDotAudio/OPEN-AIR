import sys
import tkinter as tk
from loguru import logger

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
        
        # Apply OS-specific window maximization logic and handle errors gracefully
        logger.debug("Attempting to set window maximization attributes...")
        try:
            if sys.platform.startswith("linux"):
                root.attributes("-zoomed", True)
                logger.debug("Set '-zoomed' attribute for Linux.")
            else:
                root.state("zoomed")
                logger.debug("Set 'zoomed' state for non-Linux.")
            
            # Ensure window is updated after setting state/attributes
            root.update_idletasks()

        except tk.TclError as e:
            # Log TclErrors specifically related to window attributes/geometry
            logger.error(f"🖥️🎨 [UI] TclError during window maximization/state setting: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Fallback to setting geometry if maximization fails
            logger.debug("Maximization failed. Falling back to setting window geometry...")
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            root.geometry(f"{sw}x{sh}+0+0")
            logger.debug(f"Set fallback geometry to {sw}x{sh}+0+0.")
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"🖥️🎨 [UI] Unexpected error during window attribute/geometry setting: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Fallback geometry as a last resort
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            root.geometry(f"{sw}x{sh}+0+0")
            logger.debug(f"Set fallback geometry due to unexpected error to {sw}x{sh}+0+0.")
        
        root.withdraw()
        return root

    @staticmethod
    def reveal_main_window(root, splash, debug_enabled):
        if debug_enabled: logger.debug("🖥️🎨 [UI] Reveal main window.")
        root.deiconify()
        splash.hide()
