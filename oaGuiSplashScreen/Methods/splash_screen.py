import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Methods/splash_screen.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized Application Splash Screen.

import tkinter as tk
from tkinter import ttk
from oaLogging.Entry import logger, vocal_capture

LOCAL_DEBUG = True

# --- Standard Debug Logging Setup ---

# --- EXTRACTED CORE MODULES ---
from ..Core.gif_animator import GifAnimator
from ..Core.lyric import LyricManager

class SplashScreen:
    """Manages the lifecycle and display of the animated application splash screen."""

    def __init__(self, parent, app_version, debug_enabled):
        self.parent, self.app_version, self.debug_enabled = parent, app_version, debug_enabled
        self.status_label = None
        
        # 1. Window Setup
        self.win = tk.Toplevel(parent); self.win.overrideredirect(True); self.win.configure(bg="black")
        
        w, h = 600, 470
        sw, sh = parent.winfo_screenwidth(), parent.winfo_screenheight()
        self.win.geometry(f"{w}x{h}+{(sw//2)-(w//2)}+{(sh//2)-(h//2)+200}")

        # 2. UI Layout
        main = tk.Frame(self.win, bg="black"); main.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        header = tk.Frame(main, bg="black"); header.pack(side=tk.TOP, pady=(0, 5))
        tk.Label(header, text="Open ", font=("Helvetica", 36), fg="#FF6B35", bg="black").pack(side=tk.LEFT)
        tk.Label(header, text="Air", font=("Helvetica", 36, "bold"), fg="#33A1FD", bg="black").pack(side=tk.LEFT)
        tk.Label(main, text="Zone Awareness Processor", font=("Helvetica", 14), fg="white", bg="black").pack(pady=(0, 5))

        vis = tk.Frame(main, bg="black", height=250); vis.pack(fill=tk.X, pady=5); vis.pack_propagate(False)
        self.gif_lbl = tk.Label(vis, bg="black"); self.gif_lbl.pack(expand=True)
        
        self.lyrics_lbl = tk.Label(main, text="", fg="gray", bg="black", font=("Helvetica", 10, "italic"))
        self.lyrics_lbl.pack(side=tk.BOTTOM, pady=(5, 0))

        # 3. Component Engines
        self.animator = GifAnimator(self.win, self.gif_lbl)
        self.lyrics = LyricManager(self.lyrics_lbl)
        
        if self.animator.load("splash_logo.gif"):
            self.animator.start(on_loop_callback=self.lyrics.cycle)
        else:
            tk.Label(vis, text="[Animation Offline]", fg="#333", bg="black").pack(expand=True)

        if LOCAL_DEBUG:
            matrix_log("ui", "gui_manager", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅ SplashScreen materialised.", "DEBUG")

    def set_status(self, message):
        """Updates the startup status text and pumps the Tkinter event loop."""
        matrix_log("ui", "gui_manager", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔬 SPLASH: {message}", "DEBUG")
        if not self.win or not self.win.winfo_exists(): return
        
        if not self.status_label:
            self.status_label = tk.Label(self.win, bg="black", fg="#33A1FD", font=("Arial", 10, "bold"))
            self.status_label.place(relx=0.5, rely=0.8, anchor="center")
        
        self.status_label.config(text=message)
        try: 
            self.win.update()
            self.win.update_idletasks()
        except Exception as e:
            # 🔬 SPLASH: Silently ignoring update error (possibly destroyed) but vocalizing it
            vocal_capture("UI", f"SplashScreen: Update failure: {e}")

    def hide(self):
        """Safely dismisses the splash screen."""
        if self.win and self.win.winfo_exists():
            self.animator.stop(); self.win.destroy(); self.win = None
            if LOCAL_DEBUG:
                matrix_log("ui", "gui_manager", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "👋 SplashScreen dismissed.", "DEBUG")
