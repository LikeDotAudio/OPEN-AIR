import tkinter as tk
from oaComMidi.Interface.midi_dashboard import MidiDashboard

def test():
    root = tk.Tk()
    try:
        # Create a mock midi_manager or just let it fail finding it
        frame = tk.Frame(root)
        frame.midi_manager = None
        
        dash = MidiDashboard(frame)
        dash.pack()
        print("✅ MidiDashboard instantiated successfully")
        
        # Check if keyboard and log_text exist
        if hasattr(dash, 'keyboard'):
            print("✅ Keyboard exists")
        if hasattr(dash, 'log_text'):
            print("✅ Log text exists")
            
    except Exception as e:
        print(f"❌ Failed to instantiate MidiDashboard: {e}")
        import traceback
        traceback.print_exc()
    finally:
        root.destroy()

if __name__ == "__main__":
    test()
