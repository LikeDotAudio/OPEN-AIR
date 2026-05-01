# oaGuiEditorWYSIWYG/Methods/builder_editor_grid.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Diagnostic grid drawing for the WYSIWYG Editor.

class BuilderEditorGrid:
    """Diagnostic grid drawing for WYSIWYG alignment."""
    @staticmethod
    def draw(canvas, scroll_frame, is_editor=False):
        """Draws a 100px diagnostic grid for WYSIWYG alignment."""
        if not is_editor or not canvas.winfo_exists(): return
        canvas.delete("editor_grid")

        w = max(canvas.winfo_width(), scroll_frame.winfo_reqwidth())
        h = max(canvas.winfo_height(), scroll_frame.winfo_reqheight())

        # ⚡ OPTIMIZATION: Use batch line creation if needed, but for editor mode this is fine.
        for x in range(0, w, 100):
            canvas.create_line(x, 0, x, h, fill="#333333", dash=(2, 4), tags="editor_grid")
        for y in range(0, h, 100):
            canvas.create_line(0, y, w, y, fill="#333333", dash=(2, 4), tags="editor_grid")

        # Center Axis
        canvas.create_line(w//2, 0, w//2, h, fill="#FF9900", width=1, dash=(5, 5), tags="editor_grid")
        canvas.create_line(0, h//2, w, h//2, fill="#FF00FF", width=1, dash=(5, 5), tags="editor_grid")
        canvas.tag_lower("editor_grid")
