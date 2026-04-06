# Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260323.1910.1
#
# Description: This file acts as the public API and orchestrator for the installation module.
# It initializes the Textual UI for the installation process.

import sys
import os

def _inject_project_root():
    """Calculates and injects the project root into sys.path."""
    # Current file: project_root/oaInstallation/Entry.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    return project_root

def main():
    """
    Entry point for the OPEN-AIR Installation Module.
    Initializes the Textual UI for the installation process.
    """
    _inject_project_root()

    try:
        # Import the Textual App from the Interface sub-module
        from oaInstallation.Interface.SetupUI import SetupApp
        app = SetupApp()
        app.run()
    except ImportError as e:
        print(f"🛑 [ERROR] Failed to load installation interface: {e}")
        print("💡 Hint: Run the legacy setup to install dependencies: python3 oaInstallation/Managers/Setup.py")
        sys.exit(1)
    except Exception as e:
        print(f"🛑 [CRITICAL] Unexpected error during installation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # If no command-line arguments are provided, default to running tests.
    # Otherwise, assume specific commands are intended (e.g., main).
    if len(sys.argv) > 1:
        print("Executing command...")
        main() 
    else:
        run_tests()

