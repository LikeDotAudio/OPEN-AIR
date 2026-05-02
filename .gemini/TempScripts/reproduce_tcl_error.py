
import os
import sys
import tkinter as tk
from unittest.mock import MagicMock, patch

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from oaGui.Core.loader_bootstrap_engine import LoaderBootstrapEngine


def main():
    root = tk.Tk()
    root.withdraw()
    mock_splash = MagicMock()
    mock_shutdown = MagicMock()
    mock_services = {
        "mqtt_conn": MagicMock(),
        "sub_router": MagicMock(),
        "state_cache": MagicMock(),
        "protocol_router": MagicMock(),
        "mirror_engine": MagicMock(),
        "splinker_manager": MagicMock()
    }
    mock_app_constants = MagicMock()
    mock_app_constants.global_settings = {"debug_enabled": False}

    engine = LoaderBootstrapEngine(root, mock_splash, mock_services, mock_app_constants, mock_shutdown)

    print("Testing IMPROVED TclError handling in _launch_app...")
    # Mock EngineGuiDisplay to raise TclError
    with patch("oaGui.Entry.EngineGuiDisplay", side_effect=tk.TclError("Simulated TclError")):
        try:
            engine._launch_app(
                mock_services["mqtt_conn"],
                mock_services["sub_router"],
                mock_services["mirror_engine"],
                mock_services["state_cache"]
            )
        except UnboundLocalError:
            print("❌ FAILURE: UnboundLocalError raised! The fix didn't work.")
        except tk.TclError:
            print("❌ FAILURE: TclError escaped! It should have been caught and logged (and shutdown triggered) inside _launch_app.")
        except Exception as e:
            # Note: _launch_app catches Exception and calls on_closing, it doesn't re-raise to the caller
            # unless we changed it. Wait, I didn't remove the outer except Exception in _launch_app.
            # So it should NOT reach here.
            print(f"❌ ERROR: Caught unexpected exception: {type(e).__name__}: {e}")
        else:
            print("✅ SUCCESS: No exception escaped _launch_app. Shutdown should have been triggered internally.")

    root.destroy()

if __name__ == "__main__":
    main()
