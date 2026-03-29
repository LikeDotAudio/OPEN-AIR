import tkinter as tk
from unittest.mock import MagicMock
import os

os.environ["DISPLAY"] = ""
try:
    root = tk.Tk()
except Exception as e:
    root = MagicMock()

try:
    var = tk.DoubleVar(master=root, value=10.0)
    print(f"var.get() = {var.get()}")
except Exception as e:
    print(f"var.get() failed: {e}")
