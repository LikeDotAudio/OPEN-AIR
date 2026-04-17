# oaGuiEditorWYSIWYG/Managers/run_builder.py
# Author: Anthony Peter Kuzub
# Version: 20260416.0230.1
#
# Description: Main entry point for the standalone WYSIWYG editor application.

import sys
import pathlib
import orjson
import tkinter as tk
import signal

from .runner.runner_env import RunnerEnvironment
from .runner.mqtt_tester import MqttTester
from .wysiwyg_editor import WysiwygEditor
from oaStyle.Managers.theme_applier import apply_theme
from oaLogging.Methods.matrix_gate import matrix_log
from oaLogging.Core.logger import WYSIWYG_LOGGER

class StandaloneRunner:
    """Orchestrates the boot sequence and lifecycle of the Standalone WYSIWYG Builder."""
    
    def __init__(self):
        self.root = None
        self.app = None
        self.json_path = None
        self.logger = WYSIWYG_LOGGER.bind(protocol="WYSIWYG")

    def run(self):
        """Main execution flow."""
        self._initialize_env()
        self._parse_args()
        config = self._load_json_data()
        
        self._setup_main_window()
        self._launch_app(config)
        self._bind_signals()
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.shutdown()

    def _initialize_env(self):
        """Bootstraps paths and logging via the environment service."""
        RunnerEnvironment.setup()

    def _parse_args(self):
        """Extracts the target JSON file from command line arguments."""
        if len(sys.argv) < 2:
            print("Usage: python run_builder.py <json_file_path>")
            sys.exit(1)
        self.json_path = pathlib.Path(sys.argv[1])
        if not self.json_path.exists():
            self.logger.error(f"Standalone Builder: File not found: {self.json_path}")
            sys.exit(1)

    def _load_json_data(self):
        """Loads and parses the target GUI definition file."""
        try:
            if self.json_path.stat().st_size > 0:
                with open(self.json_path, "rb") as f:
                    return orjson.loads(f.read())
            return {}
        except Exception as e:
            self.logger.exception(f"Standalone Builder: Load failed: {e}")
            sys.exit(1)

    def _setup_main_window(self):
        """Initializes the Tkinter root window and applies the global theme."""
        self.root = tk.Tk()
        self.root.title(f"OPEN-AIR: WYSIWYG Editor - {self.json_path.name}")
        self.root.geometry("1400x900")
        apply_theme(self.root)

    def _launch_app(self, config_data):
        """Instantiates the core editor controller."""
        self.app = WysiwygEditor(
            parent_window=self.root,
            config_data=config_data,
            json_filepath=self.json_path,
            on_test_callback=self._handle_test_request,
            is_standalone=True,
        )

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
        matrix_log("ui", "gui_builder", "exit", "🚀 [LAUNCHING] Standalone Builder: Program exiting.", "INFO")
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
            matrix_log("ui", "gui_builder", "exit", f"❌ Error during shutdown: {e}", "ERROR")
            sys.exit(1)

def main():
    runner = StandaloneRunner()
    runner.run()

if __name__ == "__main__":
    main()
