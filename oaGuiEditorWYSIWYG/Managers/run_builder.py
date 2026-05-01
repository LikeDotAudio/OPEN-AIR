# oaGuiEditorWYSIWYG/Managers/run_builder.py
# Author: Anthony Peter Kuzub
# Version: 20260416.0230.1
#
# Description: Main entry point for the standalone WYSIWYG editor application.

import pathlib
import signal
import sys
import tkinter as tk

# ⚡ BOOTSTRAP: Resolve project root and add to sys.path before any project imports
project_root = pathlib.Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import orjson

from oaLogging.Methods.matrix_gate import matrix_log
from oaGuiEditorWYSIWYG.Managers.runner.runner_env import RunnerEnvironment
from oaLogging.Core.logger import WYSIWYG_LOGGER
from oaStyle.Managers.theme_applier import apply_theme
from oaGuiEditorWYSIWYG.Managers.wysiwyg_editor import WysiwygEditor
from oaGuiEditorWYSIWYG.Managers.runner.mqtt_tester import MqttTester

class StandaloneRunner:
    """Orchestrates the boot sequence and lifecycle of the Standalone WYSIWYG Builder."""

    def __init__(self):
        self.root = None
        self.app = None
        self.json_path = None

    def run(self):
        """Main execution flow."""
        # 1. Setup Environment
        config = RunnerEnvironment.setup()

        self.logger = WYSIWYG_LOGGER.bind(protocol="WYSIWYG")

        self._parse_args()

        # 3. GUI Setup
        self.root = tk.Tk()
        self.root.title(f"OPEN-AIR: WYSIWYG Editor - {self.json_path.name}")
        self.root.geometry("1400x900")
        apply_theme(self.root)

        # 4. Launch App
        self.app = WysiwygEditor(
            parent_window=self.root,
            config_data=self._load_json_data(),
            json_filepath=self.json_path,
            on_test_callback=self._handle_test_request,
            is_standalone=True,
        )

        self._bind_signals()

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.shutdown()

    def _parse_args(self):
        """Extracts the target JSON file from command line arguments."""
        if len(sys.argv) < 2:
            print("Usage: python run_builder.py <json_file_path>")
            sys.exit(1)
        self.json_path = pathlib.Path(sys.argv[1])
        if not self.json_path.exists():
            print(f"❌ Standalone Builder: File not found: {self.json_path}")
            sys.exit(1)

    def _load_json_data(self):
        """Loads and parses the target GUI definition file."""
        try:
            if self.json_path.stat().st_size > 0:
                with open(self.json_path, "rb") as f:
                    return orjson.loads(f.read())
            return {}
        except Exception as e:
            print(f"❌ Standalone Builder: Load failed: {e}")
            sys.exit(1)

    def _handle_test_request(self, new_data):
        """Relays editor 'Test' events to the MQTT test bridge."""
        MqttTester.publish_rebuild(self.json_path, new_data)

    def _bind_signals(self):
        """Wires up OS signals and window close events for clean shutdown."""
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
        signal.signal(signal.SIGTERM, lambda s, f: self.root.after(0, self.shutdown))
        signal.signal(signal.SIGINT, lambda s, f: self.root.after(0, self.shutdown))

    def shutdown(self):
        """Gracefully stops all editor services and exits."""
        matrix_log("ui", "gui_builder", "exit", "🚀🚀🚀 [LAUNCHING] Standalone Builder: Program exiting.", "INFO")
        try:
            if hasattr(self, 'app') and self.app:
                self.app.shutdown()

            if self.root:
                # Check if root still exists before destroying
                try:
                    if self.root.winfo_exists():
                        self.root.destroy()
                except tk.TclError:
                    pass # Already destroyed

            sys.exit(0)
        except SystemExit:
            raise
        except Exception as e:
            matrix_log("ui", "gui_builder", "exit", f"👽🤦‍♂️🔥 [UNKNOWN] Error during shutdown: {e}", "ERROR")
            sys.exit(1)

def main():
    runner = StandaloneRunner()
    runner.run()

if __name__ == "__main__":
    main()
