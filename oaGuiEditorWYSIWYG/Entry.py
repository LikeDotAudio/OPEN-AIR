# oaGuiEditorWYSIWYG/Entry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.1
#
# Description: Gatekeeper for the oaGuiEditorWYSIWYG module.

"""
oaGuiEditorWYSIWYG/Entry.py - Gatekeeper for oaGuiEditorWYSIWYG
"""

from .Managers.wysiwyg_editor import WysiwygEditor

def launch_editor(parent_window, **kwargs):
    """
    Standard entry point to launch the WYSIWYG Editor.
    """
    return WysiwygEditor.launch(parent_window, **kwargs)

if __name__ == "__main__":
    import tkinter as tk
    root = tk.Tk()
    launch_editor(root, is_standalone=True)
    root.mainloop()
