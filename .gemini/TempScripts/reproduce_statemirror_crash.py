
import sys
import tkinter as tk
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from oaStateCache.Core.state_mirror_engine import StateMirrorEngine


def reproduce_fix():
    print("Testing StateMirrorEngine.register_widget with None tk_variable...")
    # Mock dependencies
    mock_root = tk.Tk()
    mock_subscriber_router = None
    mock_state_cache_manager = None
    base_topic = "test/topic"

    engine = StateMirrorEngine(base_topic, mock_subscriber_router, mock_root, mock_state_cache_manager)

    try:
        # This used to crash with AttributeError: 'NoneType' object has no attribute 'trace_add'
        engine.register_widget("test_path", None, "test_tab", {"type": "TestWidget"})
        print("✅ SUCCESS: register_widget handled None tk_variable correctly.")
    except AttributeError as e:
        print(f"❌ FAILURE: register_widget crashed with AttributeError: {e}")
    except Exception as e:
        print(f"❌ FAILURE: register_widget crashed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        mock_root.destroy()

if __name__ == "__main__":
    reproduce_fix()
