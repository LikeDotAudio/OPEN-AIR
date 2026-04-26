import sys

sys.path.insert(0, '/home/anthony/Documents/OPEN-AIR')
import tkinter as tk
from unittest.mock import MagicMock

from oaGuiElements.Core.graphing.Methods.dynamic_graph import GraphPlotter

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

root = tk.Tk()
plotter = GraphPlotter(root, config, 'OPEN-AIR/test', 'test_graph', state_mirror_engine=MagicMock())
plotter.pack()

plotter._perform_scheduled_update()

print("Line sig_a data:", plotter.lines['sig_a'].get_data())

