
import tkinter as tk
from oaGuiElements.Core.utils.listbox.listbox import BuilderListboxCreator

def test_make():
    root = tk.Tk()
    config = {"label_active": "Test Listbox", "path": "test/path"}
    app_instance = type('App', (object,), {})()
    # The make method should work without needing an instance of the creator
    widget = BuilderListboxCreator.make(root, config, app_instance=app_instance)
    print(f"Widget created: {widget}")
    assert isinstance(widget, tk.Canvas)
    root.destroy()
    print("Test passed!")

if __name__ == "__main__":
    test_make()
