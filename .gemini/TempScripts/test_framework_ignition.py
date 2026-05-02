# .gemini/TempScripts/test_framework_ignition.py
# Author: Gemini (Collaborator)
# Version: 20260405.2230.1
#
# Description: Verifies the consolidated oaGui ignition.

import pathlib
import sys
import tkinter as tk

# Ensure project root is in sys.path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_ignition():
    print("🚀 [TEST] Starting oaGui Ignition Test...")

    try:
        from oaGui.Entry import EngineGuiDisplay
        print("✅ [TEST] Successfully imported EngineGuiDisplay from oaGui.")
    except ImportError as e:
        print(f"❌ [TEST] Failed to import EngineGuiDisplay: {e}")
        return False

    root = tk.Tk()
    root.withdraw() # Hide main window

    print("🏗️ [TEST] Attempting to instantiate EngineGuiDisplay (Dry Run)...")
    try:
        # Mock dependencies
        app = EngineGuiDisplay(
            parent=root,
            root=root,
            mqtt_connection_manager=None,
            subscriber_router=None,
            state_mirror_engine=None,
            state_cache_manager=None
        )
        print("✅ [TEST] EngineGuiDisplay instantiated successfully.")

        # Check for key attributes/mixins
        if hasattr(app, '_build_from_directory'):
            print("✅ [TEST] FolderRecursiveScannerMixin detected.")
        else:
            print("❌ [TEST] FolderRecursiveScannerMixin MISSING!")

        if hasattr(app, 'layout_parser'):
            print("✅ [TEST] FolderLayoutInterpreter detected.")
        else:
            print("❌ [TEST] FolderLayoutInterpreter MISSING!")

        return True
    except Exception as e:
        print(f"❌ [TEST] EngineGuiDisplay instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_ignition()
    sys.exit(0 if success else 1)
