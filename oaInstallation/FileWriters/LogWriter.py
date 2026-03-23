# FileWriters/LogWriter.py
# Author: Anthony Peter Kuzub
# Version: 20260323.1925.1
#
# Description: Handles persistent logging of the installation process.

import os
import datetime

class InstallationLogWriter:
    """
    Writer for saving installation process logs to the configuration directory.
    """
    def __init__(self):
        # Resolve project root
        # Current file: project_root/oaInstallation/FileWriters/LogWriter.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(os.path.dirname(current_dir))
        self.log_dir = os.path.join(self.project_root, "oaConfiguration")
        self.log_file = os.path.join(self.log_dir, "installation_log.txt")

    def ensure_log_dir(self):
        """Ensures the target log directory exists."""
        if not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir)
                return True
            except Exception:
                return False
        return True

    def write_log(self, log_content: str):
        """
        Appends the provided log content to the installation log file.
        Includes a timestamp for the session.
        """
        if not self.ensure_log_dir():
            return False

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_file, "a") as f:
                f.write(f"\n--- INSTALLATION SESSION: {timestamp} ---\n")
                f.write(log_content)
                f.write("\n-------------------------------------------\n")
            return True
        except Exception:
            return False

    def get_log_path(self):
        """Returns the absolute path to the log file."""
        return self.log_file
