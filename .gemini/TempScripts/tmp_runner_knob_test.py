import sys
import tkinter as tk

sys.path.insert(0, '/home/anthony/Documents/OPEN-AIR')

from oaGuiElements.Core.Knobs.knob.Core.knob_renderer import draw_knob_visuals

root = tk.Tk()
canvas = tk.Canvas(root, width=200, height=200)
canvas.pack()

try:
    config = {
        "shape": "gear",
        "teeth": 8,
        "bg_start": 0,
        "bg_extent": 360,
        "style": "standard",
        "pointer_style": "triangle",
        "pointer_length": 10,
        "pointer_offset": 5,
        "pointer_color": "white",
        "no_center": False
    }
    draw_knob_visuals(canvas, 100, 100, 200, 200, 0, 100, 50, config, "gray", "blue", "gray", 0, 0, 0, 0)
    print("SUCCESS: draw_knob_visuals completed without IndexError.")
except Exception as e:
    print(f"FAILED: {type(e).__name__} - {e}")
    import traceback
    traceback.print_exc()

root.destroy()
