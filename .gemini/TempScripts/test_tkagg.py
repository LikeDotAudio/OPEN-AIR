import sys
import os
sys.path.insert(0, '/home/anthony/Documents/OPEN-AIR')

import tkinter as tk
from unittest.mock import MagicMock
from oaGuiElements.Core.graphing.Methods.dynamic_graph import GraphPlotter
import time

def run_test():
    root = tk.Tk()
    root.geometry("800x600")

    config = {
        "Navigation": { "enable_pan": True, "enable_zoom": True },
        "axis": {
            "x": { "label": "Time", "scale": "linear", "min": 0, "max": 1 },
            "y": { "label": "Amplitude", "scale": "linear", "min": -1.5, "max": 1.5 }
        },
        "datasets": [
            { "id": "sig_a", "initial_csv_data": "x,y\n0,0\n0.5,0.5\n1,1", "label": "Sig A" }
        ],
        "geometry": { "width": 800, "height": 400 },
        "id": "test_graph", "type": "plot_widget"
    }

    mock_context = MagicMock()
    mock_context.state_mirror_engine = MagicMock()
    mock_context.subscriber_router = MagicMock()
    mock_context.base_mqtt_topic_from_path = 'OPEN-AIR/test'
    mock_context.builder_instance = MagicMock()

    plotter = GraphPlotter(root, config, 'OPEN-AIR/test', 'test_graph', context=mock_context)
    plotter.pack(fill="both", expand=True)

    # Force initial draw
    plotter._perform_scheduled_update()
    
    # Save the canvas as a postscript or just print if it exists
    print("Canvas drawn. Exists:", plotter.canvas.get_tk_widget().winfo_exists())
    
    # We won't call mainloop to avoid hanging, we just update
    root.update()
    time.sleep(1)
    print("Canvas width:", plotter.canvas.get_tk_widget().winfo_width())
    print("Canvas height:", plotter.canvas.get_tk_widget().winfo_height())
    
    root.destroy()

if __name__ == "__main__":
    run_test()
