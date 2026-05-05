# Hooks/context_menu.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Modular.1
#
# Description: Context Menu orchestrator for the Dynamic Builder.
# Handles interactive designer tools (WYSIWYG) and dependency auditing.

import subprocess
import sys
import tkinter as tk
from pathlib import Path

from oaLogging.Core.logger import builder_logger


class BuilderContextMenuMixin:
    """
    Mixin providing right-click design-time tools.
    Encapsulates external process management for the WYSIWYG editor.
    """
    _editor_process = None
    _editor_file = None

    def _setup_context_menu(self):
        """Initializes the Tkinter Menu and binds physical button events."""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.populate_context_menu(self.context_menu)

        # Physical Bindings
        target_widgets = [w for w in ['canvas', 'scroll_frame'] if getattr(self, w, None) is not None]
        for attr in target_widgets:
            getattr(self, attr).bind("<Button-3>", self._on_right_click)

    def populate_context_menu(self, menu):
        """Appends the builder context menu items to an existing menu."""
        menu.add_command(label="WYSIWYG Editor", command=self._launch_wysiwyg_editor)
        menu.add_command(label="Check Dependencies", command=self._run_dependency_audit)
        menu.add_separator()
        menu.add_command(label="Reload UI", command=self._force_rebuild_gui)

    def bind_context_menu(self, widget):
        """Standard API to attach the builder context menu to any UI element."""
        if hasattr(self, 'context_menu') and self.context_menu:
            widget.bind("<Button-3>", self._on_right_click, add="+")

    def _on_right_click(self, event):
        """Displays the popup menu at the mouse pointer root coordinates."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            builder_logger.error(f"🍔🔽🖱️ Context Menu Failure: {e}")
        finally:
            self.context_menu.grab_release()

    def _launch_wysiwyg_editor(self):
        """
        Orchestrates the spawning of the external WYSIWYG editor process.
        Ensures a singleton process per file.
        """
        if not hasattr(self, 'json_filepath') or not self.json_filepath:
            builder_logger.error("🏗️🚫 Editor launch failed: No target JSON file found.")
            return

        if self._is_editor_active():
            if str(self._editor_file) == str(self.json_filepath):
                return # Already editing this file
            self._terminate_active_editor()

        self._spawn_editor_process()

    def _show_wysiwyg_editor(self):
        """Alias for compatibility with the tab editor launcher."""
        self._launch_wysiwyg_editor()

    def _is_editor_active(self):
        """Checks if a previously spawned editor is still running."""
        return self._editor_process and self._editor_process.poll() is None

    def _terminate_active_editor(self):
        """Gracefully shuts down the current editor process."""
        try:
            self._editor_process.terminate()
            self._editor_process.wait(timeout=1.0)
        except Exception:
            self._editor_process.kill()
        self._editor_process = None

    def _spawn_editor_process(self):
        """Physical execution of the subprocess call for the editor."""
        runner_path = Path(__file__).resolve().parent.parent.parent.parent / "oaGuiEditorWYSIWYG" / "Managers" / "run_builder.py"

        if not runner_path.exists():
            builder_logger.error(f"🏗️🚫 Orchestrator runner missing: {runner_path}")
            return

        try:
            # ⚡ FORENSIC LOGGING: Capture stderr to identify why the process might fail to start
            BuilderContextMenuMixin._editor_process = subprocess.Popen(
                [sys.executable, str(runner_path), str(self.json_filepath)],
                stderr=subprocess.PIPE,
                text=True
            )
            BuilderContextMenuMixin._editor_file = self.json_filepath
            
            # Check for immediate failure
            try:
                _, stderr = BuilderContextMenuMixin._editor_process.communicate(timeout=0.5)
                if stderr:
                    builder_logger.error(f"🏗️🚫 Editor Process Immediate Error: {stderr.strip()}")
            except subprocess.TimeoutExpired:
                # Process is still running, which is good
                pass

        except Exception as e:
            builder_logger.exception(f"🏗️🚫 Process spawn failure: {e}")

    def _run_dependency_audit(self):
        """Triggers the global installation script to verify system state."""
        from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
        audit_script = GLOBAL_PROJECT_ROOT / "oaInstallation" / "Entry.py"

        if not audit_script.exists():
            builder_logger.error("🏗️🚫 Audit script not found.")
            return

        try:
            subprocess.run([sys.executable, str(audit_script)], check=False)
        except Exception as e:
            builder_logger.error(f"🏗️🚫 Dependency audit failed: {e}")
