# Core/context_menu.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import time
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import builder_logger

class BuilderContextMenuMixin:
    """
    Handles context menu operations for the DynamicGuiBuilder,
    including launching the WYSIWYG editor and checking dependencies.
    """
    _editor_process = None
    _editor_file = None

    def _setup_context_menu(self):
        if LOCAL_DEBUG: builder_logger.trace("🍔🔽🖱️ [UI] Configuring right-click context menu.")
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="WYSIWYG Editor", command=self._show_wysiwyg_editor)
        self.context_menu.add_command(label="Check Dependencies", command=self._check_dependencies)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Reload", command=self._force_rebuild_gui)
        
        # Bind right-click to canvas and scroll frame
        if hasattr(self, 'canvas'):
            self.canvas.bind("<Button-3>", self._on_right_click)
        if hasattr(self, 'scroll_frame'):
            self.scroll_frame.bind("<Button-3>", self._on_right_click)

    def bind_to_widget(self, widget):
        """Binds the context menu to a specific widget."""
        if hasattr(self, 'context_menu') and self.context_menu:
            widget.bind("<Button-3>", self._on_right_click, add="+")

    def _on_right_click(self, event):
        """Displays context menu on right click."""
        if LOCAL_DEBUG:
            builder_logger.debug(f"🍔🔽🖱️ Right-click detected on widget: {event.widget}")
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            builder_logger.exception(f"🍔🔽🖱️💥 Failed to show context menu: {e}")
        finally:
            self.context_menu.grab_release()

    def _show_wysiwyg_editor(self):
        """Opens the WYSIWYG Editor in a separate process, ensuring only ONE instance exists system-wide."""
        import subprocess
        import sys
        
        if not hasattr(self, 'json_filepath') or not self.json_filepath:
            builder_logger.error("🏗️🚫🛑 [BUILDER] DynamicGuiBuilder: Cannot launch editor without a valid JSON file path.")
            return

        # ⚡ SINGLETON CHECK: Verify if an editor process is already running
        if BuilderContextMenuMixin._editor_process:
            # Check if process is still alive
            if BuilderContextMenuMixin._editor_process.poll() is None:
                # Still running. Is it the same file?
                if str(BuilderContextMenuMixin._editor_file) == str(self.json_filepath):
                    if LOCAL_DEBUG: builder_logger.info(f"🏗️📂⚠️ [BUILDER] Editor already active for '{self.json_filepath.name}'. Refocusing is up to the OS.")
                    return
                else:
                    # Different file requested. Close the old one first.
                    if LOCAL_DEBUG: builder_logger.info(f"🏗️📂♻️ [BUILDER] Closing previous editor for '{BuilderContextMenuMixin._editor_file.name}' to open '{self.json_filepath.name}'.")
                    try:
                        BuilderContextMenuMixin._editor_process.terminate()
                        BuilderContextMenuMixin._editor_process.wait(timeout=1.0)
                    except Exception as e:
                        builder_logger.warning(f"🏗️🚫⚠️ [BUILDER] Failed to gracefully close previous editor: {e}")
                        BuilderContextMenuMixin._editor_process.kill()
            
            # Clear state for a fresh spawn
            BuilderContextMenuMixin._editor_process = None
            BuilderContextMenuMixin._editor_file = None

        if LOCAL_DEBUG: builder_logger.info(f"🏗️🚀💻 [BUILDER] DynamicGuiBuilder: Launching standalone WYSIWYG Editor process for {self.json_filepath}")
        
        # Path to the standalone runner
        # ⚡ CORRECTED: Point to the actual location in oaGuiEditorWYSIWYG
        runner_path = Path(__file__).resolve().parent.parent.parent / "oaGuiEditorWYSIWYG" / "Managers" / "run_builder.py"
        
        # ⚡ GRAVITY OF ERRORS: Explicit check before spawning
        if not runner_path.exists():
            builder_logger.error(f"🏗️🚫🛑 [BUILDER] CRITICAL: Standalone runner not found at {runner_path}")
            return

        try:
            # Launch as a separate process and track it globally
            BuilderContextMenuMixin._editor_process = subprocess.Popen([
                sys.executable, 
                str(runner_path), 
                str(self.json_filepath)
            ])
            BuilderContextMenuMixin._editor_file = self.json_filepath
            
            if LOCAL_DEBUG: builder_logger.success("🏗️🆗✅ [BUILDER] DynamicGuiBuilder: Standalone process spawned successfully.")
        except Exception as e:
            # ⚡ GRAVITY OF ERRORS: Log regardless of LOCAL_DEBUG
            builder_logger.exception("🏗️🚫🛑 [ERROR] DynamicGuiBuilder Error: Failed to launch standalone editor")
            BuilderContextMenuMixin._editor_process = None
            BuilderContextMenuMixin._editor_file = None

    def _check_dependencies(self):
        """Manually triggers the Installation/Setup script to verify dependencies."""
        from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
        setup_path = GLOBAL_PROJECT_ROOT / "oaInstallation" / "Entry.py"
        
        if not setup_path.exists():
            builder_logger.error(f"🏗️🚫🛑 [BUILDER] Setup script not found at {setup_path}")
            return

        if LOCAL_DEBUG: builder_logger.info("🏗️🚀📦 [BUILDER] Launching Installation/Setup.py...")
        
        import subprocess
        import sys
        try:
            # Run setup and wait for completion
            result = subprocess.run([sys.executable, str(setup_path)], check=False)
            if result.returncode == 0:
                if LOCAL_DEBUG: builder_logger.success("🏗️🆗✅ [BUILDER] Dependency check/Setup completed successfully.")
            else:
                builder_logger.error(f"🏗️🚫🛑 [BUILDER] Setup failed with exit code {result.returncode}")
        except Exception as e:
            builder_logger.exception("🏗️🚫🛑 [ERROR] DynamicGuiBuilder: Failed to launch setup script")
