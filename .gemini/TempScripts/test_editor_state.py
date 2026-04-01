import sys
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaGuiEditorWYSIWYG.Core.state import StateManager
from oaGuiEditorWYSIWYG.Core.event_bus import event_bus

def test_editor_state():
    state = StateManager()
    
    initial = {"window": {"width": 800, "height": 600}, "widgets": {"w1": {"type": "button"}}}
    
    print("Initializing...")
    state.initialize(initial)
    
    current = state.get_state()
    print(f"Current state: {current}")
    
    print("Updating state...")
    state.update_state({"type": "slider"}, "widgets.w1")
    
    updated = state.get_state()
    print(f"Updated state: {updated}")
    
    print("Batch updating...")
    state.batch_update([
        (1024, "window.width"),
        ({"type": "knob"}, "widgets.w2")
    ])
    
    batched = state.get_state()
    print(f"Batched state: {batched}")
    
    if batched["window"]["width"] == 1024 and batched["widgets"]["w2"]["type"] == "knob":
        print("✅ SUCCESS: Editor State Manager is functional via Rust backend.")
    else:
        print("❌ FAILURE: State update mismatch.")

if __name__ == "__main__":
    test_editor_state()
