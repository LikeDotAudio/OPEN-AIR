import pathlib
import tkinter as tk
from oaGuiManager.FileReaders.module_loader import ModuleLoader

def test():
    root = tk.Tk()
    loader = ModuleLoader(theme_colors={}, app_instance=None)
    path = pathlib.Path("oaGuiDefinitions/Assets/right_50/bottom_90/50_MIDI/midi.py")
    
    cls = loader.load_module_from_path(path)
    print(f"Class found: {cls.__name__ if cls else 'None'}")
    if cls:
        print(f"Class source: {cls.__module__}")
    
    root.destroy()

if __name__ == "__main__":
    test()
