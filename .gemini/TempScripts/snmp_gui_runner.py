# .gemini/TempScripts/snmp_gui_runner.py
# Author: Gemini (Collaborator)
# Version: 20260415.0104.1
#
# Description: Temporary script to demonstrate standalone Tkinter GUI for SNMP modules.

import os
import sys
import tkinter as tk

# Ensure project root is in sys.path for direct execution
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the SNMP GUI component
from oaComProtocols.oaComSNMP.Entry import start, stop
from oaComProtocols.oaComSNMP.Interface.snmp_log_impl import SnmpLogImplementation


class SnmpGuiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SNMP Monitor GUI")
        self.geometry("1000x800")

        # Start the SNMP backend manager first
        # This will also run the self-tests thanks to the recent change
        self.snmp_manager = start(run_bridge=True)
        if not self.snmp_manager:
            print("ERROR: Failed to start SNMP Manager. Exiting GUI.")
            self.destroy()
            return

        # Instantiate the SnmpLogImplementation
        self.snmp_log_frame = SnmpLogImplementation(self, app_instance=self)
        self.snmp_log_frame.pack(fill=tk.BOTH, expand=True)

        # Pass the manager to the GUI frame
        self.snmp_log_frame.snmp_manager = self.snmp_manager

        # Handle window closing to stop the SNMP manager gracefully
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        print("Closing GUI and stopping SNMP Manager...")
        if self.snmp_manager:
            stop()
        self.destroy()

if __name__ == "__main__":
    app = SnmpGuiApp()
    app.mainloop()
