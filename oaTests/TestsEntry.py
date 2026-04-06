# Entry.py
# Author: Anthony Peter Kuzub
# Version: 20260406.1045.1
#
# Description: Public API and orchestrator for the OPEN-AIR Testing Module.
# Initializes the Textual UI for test execution and maintenance.

import sys
import os

def _inject_project_root():
    """Calculates and injects the project root into sys.path."""
    # Current file: project_root/oaTests/Entry.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    return project_root

def main():
    """
    Entry point for the OPEN-AIR Testing Module.
    Initializes the Textual UI for test management.
    """
    project_root = _inject_project_root()

    try:
        # Initialize specialized test logging
        from oaLogging.Entry import initialize_test_logging, TEST_LOGGER
        test_log_dir = os.path.join(project_root, "oaDataLogs", "TestLog")
        initialize_test_logging(test_log_dir)
        TEST_LOGGER.info("🧪 [INIT] Test Logging System Online.")

        # Import the Textual App from the Interface sub-module
        from oaTests.Interface.TestsUI import TestsApp
        app = TestsApp(project_root)
        app.run()
    except ImportError as e:
        print(f"🛑 [ERROR] Failed to load testing interface: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"🛑 [CRITICAL] Unexpected error during test suite execution: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
