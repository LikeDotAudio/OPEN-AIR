# splash_screen/splash_screen.py
#
# This module defines the SplashScreen class, which displays an animated splash screen with version information and status updates during application startup.
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
# Version 20250821.200641.1

import tkinter as tk
from tkinter import ttk
import os
import sys
import pathlib
import traceback

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

# --- Image Library Imports ---
try:
    from PIL import Image, ImageTk

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: Pillow (PIL) not found. GIF animation will be disabled.")

# --- Path Setup ---
SPLASH_ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent

# Import lyrics data
try:
    from . import lyrics_data

    LYRICS_AVAILABLE = True
except ImportError:
    lyrics_data = None
    LYRICS_AVAILABLE = False


class SplashScreen:
    # Initializes the SplashScreen.
    # This constructor sets up the top-level splash window, configures its appearance,
    # dimensions, and position. It also initializes the GIF animation and lyric display,
    # and includes mechanisms for safe logging.
    # Inputs:
    #     parent: The parent Tkinter widget (usually the main root window).
    #     app_version (str): The current version string of the application.
    #     debug_enabled (bool): A flag indicating if debug logging is enabled.
    # Outputs:
    #     None.
    def __init__(self, parent, app_version, debug_enabled):
        self.debug_enabled = debug_enabled

        self._safe_log(
            f"🖥️🟢 Entering SplashScreen.__init__"
        )  # Removed force_print=True

        self.parent = parent
        self.app_version = app_version

        self.gif_frames = []
        self.photo_images = []  # Initialize to prevent AttributeError
        self.gif_frame_index = 0
        self.gif_animation_job = None
        self.status_label = None  # Initialize to None

        try:
            self.splash_window = tk.Toplevel(self.parent)
            self.splash_window.overrideredirect(True)
            self.splash_window.attributes("-alpha", 1.0)  # Always full opacity
            self.splash_window.configure(bg="black")

            # --- Dimensions & Centering (TIGHTENED) ---
            win_width, win_height = 600, 470
            screen_width = self.parent.winfo_screenwidth()
            screen_height = self.parent.winfo_screenheight()
            x = (screen_width // 2) - (win_width // 2)
            y = (screen_height // 2) - (win_height // 2) + 200
            self.splash_window.geometry(f"{win_width}x{win_height}+{x}+{y}")

            self.main_content_frame = tk.Frame(self.splash_window, bg="black")
            self.main_content_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)

            # --- 1. Header (TIGHTENED) ---
            header_frame = tk.Frame(self.main_content_frame, bg="black")
            header_frame.pack(side=tk.TOP, pady=(0, 5))

            tk.Label(
                header_frame,
                text="Open ",
                font=("Helvetica", 36, "normal"),
                fg="#FF6B35",
                bg="black",
            ).pack(side=tk.LEFT)
            tk.Label(
                header_frame,
                text="Air",
                font=("Helvetica", 36, "bold"),
                fg="#33A1FD",
                bg="black",
            ).pack(side=tk.LEFT)

            # --- 2. Sub-header (TIGHTENED) ---
            tk.Label(
                self.main_content_frame,
                text="Zone Awareness Processor",
                font=("Helvetica", 14),
                fg="white",
                bg="black",
            ).pack(side=tk.TOP, pady=(0, 5))

            # --- 3. Animation Area (TIGHTENED) ---
            vis_frame = tk.Frame(self.main_content_frame, bg="black", height=250)
            vis_frame.pack(side=tk.TOP, fill=tk.X, expand=False, pady=5)
            vis_frame.pack_propagate(False)

            if PIL_AVAILABLE:
                self._safe_log("🎬 Initializing GIF Animation...")
                try:
                    self._init_gif_animation(vis_frame)
                except Exception as e:
                    self._safe_log(f"🔴 GIF FAILED: {e}", is_error=True)
                    traceback.print_exc()
                    tk.Label(vis_frame, text="[GIF Error]", fg="red", bg="black").pack(
                        expand=True
                    )
            else:
                tk.Label(
                    vis_frame, text="[Image Libraries Missing]", fg="#333", bg="black"
                ).pack(expand=True)

            # --- 4. Lyrics (TIGHTENED) ---
            self.lyrics_label = tk.Label(
                self.main_content_frame,
                text="",
                fg="gray",
                bg="black",
                font=("Helvetica", 10, "italic"),
            )
            self.lyrics_label.pack(side=tk.BOTTOM, pady=(5, 0))

            # --- Data & Logic ---
            self.lyrics = []
            if LYRICS_AVAILABLE and hasattr(lyrics_data, "lyrics"):
                self.lyrics = lyrics_data.lyrics
            if not self.lyrics:
                self.lyrics = ["...Loading..."]

            self.lyric_index = 0
            self.current_lyric = self.lyrics[0]
            self.lyrics_label.config(text=self.current_lyric)

            # --- No fade-in, start animation directly ---
            if self.photo_images:
                self._update_gif_frame()  # Start GIF immediately

            self._safe_log("✅ SplashScreen Init Complete.")

        except Exception as e:
            self._safe_log(f"🔴 CRITICAL SPLASH ERROR: {e}", is_error=True)
            traceback.print_exc()

    def set_status(self, message):
        """Updates the status text on the splash screen and pumps the event loop."""
        if self.debug_enabled:
            logger.debug(f"🔬🏗️📝 [SPLASH] Status: {message}")
            
        if self.splash_window and self.splash_window.winfo_exists():
            # Update immediately if we are on the main thread, 
            # otherwise schedule it and pump.
            try:
                self._update_status_label(message)
                self.splash_window.update()
                self.splash_window.update_idletasks()
            except Exception:
                # Fallback for thread-safety if called from background
                self.splash_window.after(0, lambda: self._update_status_label(message))

    def _update_status_label(self, message):
        """Internal helper to update the label on the main thread."""
        if not self.status_label:
            # Lazy-create the status label if it doesn't exist yet
            self.status_label = tk.Label(
                self.main_content_frame,
                text="",
                fg="#33A1FD",
                bg="black",
                font=("Helvetica", 10, "bold"),
            )
            self.status_label.pack(side=tk.TOP, pady=5)
        
        if self.status_label.winfo_exists():
            self.status_label.config(text=message)

    # Provides a safe way to log messages from the splash screen.
    # This method uses the provided `debug_log_func` to output messages,
    # ensuring consistent logging behavior across the application.
    # Inputs:
    #     message (str): The message to log.
    #     is_error (bool): Flag to indicate if the message is an error.
    #     force_print (bool): Flag to force printing regardless of debug status (removed).
    # Outputs:
    #     None.
    def _safe_log(self, message, is_error=False, force_print=False):
        if LOCAL_DEBUG: logger.debug(message)

    # Initializes and loads the GIF animation frames for the splash screen.
    # This method reads the `splash_logo.gif` file, extracts all its frames,
    # and stores them as `ImageTk.PhotoImage` objects for display. It handles
    # cases where the GIF file is not found or fails to load.
    # Inputs:
    #     parent_frame: The Tkinter frame where the GIF will be displayed.
    # Outputs:
    #     None.
    def _init_gif_animation(self, parent_frame):
        self.photo_images = []
        gif_path = pathlib.Path(__file__).parent / "splash_logo.gif"
        if not gif_path.exists():
            self._safe_log(f"🔴 GIF not found at {gif_path}", is_error=True)
            tk.Label(
                parent_frame, text="[splash_logo.gif not found]", fg="red", bg="black"
            ).pack(expand=True)
            return

        self.gif_label = tk.Label(parent_frame, bg="black")
        self.gif_label.pack(expand=True)

        try:
            with Image.open(gif_path) as img:
                for i in range(img.n_frames):
                    img.seek(i)
                    frame_image = img.copy().convert("RGBA")
                    photo_image = ImageTk.PhotoImage(frame_image)
                    self.photo_images.append(photo_image)

                self.gif_frame_duration = img.info.get("duration", 50)
                # Ensure minimum duration to prevent CPU starvation but keep it snappy
                if self.gif_frame_duration < 20: self.gif_frame_duration = 50
                
                # FIX: Keep a reference to the images on the label itself
                self.gif_label.photo_images = self.photo_images

        except Exception as e:
            self._safe_log(f"🔴 Failed to load GIF frames: {e}", is_error=True)

    # Updates the displayed GIF frame to create the animation effect.
    # This method cycles through the loaded GIF frames, updates the `gif_label`
    # with the next frame, and schedules itself to run again after a short delay
    # to maintain the animation. It also cycles through lyrics when the GIF loops.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def _update_gif_frame(self):
        if not self.splash_window or not self.splash_window.winfo_exists():
            return

        try:
            frame = self.photo_images[self.gif_frame_index]
            self.gif_label.config(image=frame)

            self.gif_frame_index = (self.gif_frame_index + 1) % len(self.photo_images)

            # When the GIF loops back to the first frame, cycle the lyrics.
            if self.gif_frame_index == 0 and self.lyrics:
                self.lyric_index = (self.lyric_index + 1) % len(self.lyrics)
                self.lyrics_label.config(text=self.lyrics[self.lyric_index])
            
            # ⚡ PUMP WINDOW: Force render of this frame even if thread is about to block
            self.splash_window.update_idletasks()

        except Exception as e:
            self._safe_log(f"🎞️ GIF Update Error: {e}", is_error=True)

        # Always reschedule to keep the loop alive
        self.gif_animation_job = self.splash_window.after(
            self.gif_frame_duration, self._update_gif_frame
        )

    # Hides and destroys the splash screen window.
    # This method cancels any ongoing GIF animation, destroys the `splash_window`,
    # and clears its reference, effectively removing the splash screen from display.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def hide(self):
        self._safe_log(
            "DEBUG: splash.hide() called. Attempting to dismiss splash screen."
        )
        # Ensure splash_window still exists before trying to interact with it
        if self.splash_window and self.splash_window.winfo_exists():
            try:
                if self.gif_animation_job:
                    self.splash_window.after_cancel(self.gif_animation_job)
                    self.gif_animation_job = None
            except Exception:
                pass  # Ignore errors if job already cancelled or window destroyed

            self.splash_window.destroy()  # Destroy the splash window directly
            self.splash_window = None  # Clear the reference

    # Cycles through and displays a new line of lyrics asynchronously.
    # This method updates the `lyrics_label` with the next lyric from the `lyrics` list
    # and schedules itself to run again after a delay, creating a continuous lyric display.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def cycle_lyrics_async(self):
        # This method is no longer called in init, but kept for potential future use or direct invocation
        if self.splash_window.winfo_exists() and self.lyrics:
            self.lyric_index = (self.lyric_index + 1) % len(self.lyrics)
            self.current_lyric = self.lyrics[self.lyric_index]
            self.lyrics_label.config(text=self.current_lyric)
            self.splash_window.after(1500, self.cycle_lyrics_async)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    print("Starting Standalone Test...")

    splash = SplashScreen(root, "TestVer", True)

    # Close after 10 seconds for testing
    root.after(10000, splash.hide)

    root.mainloop()
