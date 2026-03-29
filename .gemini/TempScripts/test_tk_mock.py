import tkinter as tk
from unittest.mock import MagicMock
import os

os.environ["DISPLAY"] = ""
try:
    root = tk.Tk()
except Exception as e:
    print(f"tk.Tk() failed as expected: {e}")
    root = MagicMock()

print("Attempting to create tk.DoubleVar...")
try:
    var = tk.DoubleVar(master=root)
    print("tk.DoubleVar created successfully!")
except Exception as e:
    print(f"tk.DoubleVar failed: {e}")
