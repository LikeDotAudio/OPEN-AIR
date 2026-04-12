import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# workspaces/json_editor.py
# Author: Gemini CLI
# Version: 1.0.0
#
# Description: The Code-level JSON Editor Workspace.

import tkinter as tk
from tkinter import ttk
import orjson
import re
from oaComBroker.Core.event_bus import event_bus
from ..state import state_manager

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import GUI_LOGGER as logger


class JsonEditor(tk.Frame):
    """The workspace for manual JSON editing with syntax highlighting."""

    def __init__(self, parent, is_detached=False, *args, **kwargs):
        self.is_detached = is_detached
        self.parent_widget = parent # Store the parent

        if self.is_detached:
            # If detached, create a Toplevel window and place JsonEditor inside it
            self.top_level_window = tk.Toplevel()
            super().__init__(self.top_level_window, bg="#1e1e1e", *args, **kwargs) # Initialize Frame inside Toplevel
            self.top_level_window.title("JSON Editor (Detached)")
            self.top_level_window.geometry("800x600") # Default size for detached window
            self.top_level_window.grid_rowconfigure(0, weight=1)
            self.top_level_window.grid_columnconfigure(0, weight=1)
            self.pack(in_=self.top_level_window, fill="both", expand=True) # Pack the frame into the Toplevel
        else:
            # If embedded, initialize as a Frame with the provided parent
            super().__init__(parent, bg="#1e1e1e", *args, **kwargs)
            # If the parent itself has a title method (e.g., it's a Toplevel or Tk window), set it.
            if hasattr(parent, 'title'):
                parent.title("JSON Editor")

        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"JsonEditor: Initializing workspace in {'detached' if self.is_detached else 'embedded'} mode...", "DEBUG")
        self._build_ui()
        
        # Subscribe to state updates
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "JsonEditor: Subscribing to EventBus...", "DEBUG")
        event_bus.subscribe("STATE_UPDATED", self._on_state_updated)
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)
        
        # ⚡ INITIAL SYNC: Ensure code loads even if the initial broadcast was missed
        current_state = state_manager.get_state()
        if current_state:
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "JsonEditor: Performing initial state sync...", "DEBUG")
            self._on_state_updated(current_state)

        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event):
        """Unsubscribe from event bus when widget is destroyed."""
        if event.widget == self:
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "JsonEditor: Workspace destroyed. Cleaning up subscriptions.", "INFO")
            event_bus.unsubscribe("STATE_UPDATED", self._on_state_updated)
            event_bus.unsubscribe("FOCUS_REQUESTED", self._on_focus_requested)

    # --- New helper methods for line numbers and scrolling ---

    def _pop_out_editor(self):
        """Creates a new Toplevel window with a detached JsonEditor."""
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "JsonEditor: Popping out editor to a new window.", "INFO")
        
        # Get current content
        current_content = self.text_area.get("1.0", "end-1c")
        
        # Create a new Toplevel and place a JsonEditor instance in it
        # The JsonEditor constructor will handle is_detached=True
        detached_editor = JsonEditor(self.master, is_detached=True) 
        detached_editor.pack(fill="both", expand=True)
        
        # Load current content into the detached editor
        detached_editor.text_area.delete("1.0", "end")
        detached_editor.text_area.insert("1.0", current_content)
        detached_editor._apply_highlight() # Apply syntax highlighting
        detached_editor._update_line_numbers() # Update line numbers in detached editor

    def _on_scroll(self, *args):
        """Synchronizes scrolling between text area and line numbers."""
        self.text_area.yview(*args)
        self.line_numbers.yview(*args)

    def _on_text_configure(self, event):
        """Updates line numbers when the text widget is resized."""
        self._update_line_numbers()

    def _on_text_modified(self, event=None):
        """Called when the text widget content is modified."""
        # This binding helps to update line numbers when text content changes
        # Check if the modification is due to internal changes (like highlighting)
        if not self.text_area.edit_modified():
            return
        self.text_area.edit_modified(False) # Reset the modified flag
        self._update_line_numbers()

    def _update_line_numbers(self):
        """Updates the line numbers displayed in the line_numbers widget."""
        # Make line numbers editable temporarily to insert new content
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")

        # Get the number of lines in the text area
        num_lines = int(self.text_area.index("end-1c").split('.')[0]) if self.text_area.get("1.0", "end-1c") else 0
        
        # Insert line numbers
        for i in range(1, num_lines + 1):
            self.line_numbers.insert("end", str(i) + "\n")
            
        # Make line numbers read-only again
        self.line_numbers.config(state="disabled")

        # Sync the scroll position of line numbers with the text area
        scroll_pos = self.text_area.yview()
        self.line_numbers.yview_moveto(scroll_pos[0])


    def _build_ui(self):
        """Builds the JSON editor UI."""
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "JsonEditor: Creating Editor UI components...", "DEBUG")
        
        # Header frame - common for both embedded and detached
        header = tk.Frame(self, bg="#333333", height=35)
        header.pack(side="top", fill="x")
        
        tk.Label(header, text="JSON DEFINITION EDITOR", bg="#333333", fg="white", 
                 font=("Arial", 9, "bold")).pack(side="left", padx=10, pady=5)
        
        ttk.Button(header, text="Apply Changes", command=self._apply_changes).pack(side="right", padx=5)
        ttk.Button(header, text="Format JSON", command=self._format_json).pack(side="right", padx=5)

        # Button to pop out editor (only if not already detached)
        if not self.is_detached:
            ttk.Button(header, text="Pop Out", command=self._pop_out_editor).pack(side="right", padx=5)

        # Editor area with line numbers and scrollbar
        editor_frame = tk.Frame(self, bg="#1e1e1e") # Frame to hold text_area and line_numbers
        editor_frame.pack(side="left", fill="both", expand=True)

        self.line_numbers = tk.Text(editor_frame, width=4, padx=4, takefocus=0, border=0,
                                     bg="#252526", fg="#606060", state="disabled", wrap="none")
        self.line_numbers.pack(side="left", fill="y")

        self.text_area = tk.Text(editor_frame, bg="#1e1e1e", fg="#dcdcdc", insertbackground="white",
                                 font=("Consolas", 11), wrap="none", undo=True, bd=0)
        self.text_area.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(editor_frame, orient="vertical", command=self._on_scroll)
        scrollbar.pack(side="right", fill="y")
        
        # Configure scrolling synchronization
        self.text_area.config(yscrollcommand=scrollbar.set)
        self.line_numbers.config(yscrollcommand=scrollbar.set) # Sync scroll with line numbers

        # Bindings for line number updates and scrolling
        self.text_area.bind("<KeyRelease>", self._on_key_release)
        self.text_area.bind("<MouseWheel>", self._on_scroll) # For mouse wheel scrolling
        self.text_area.bind("<Button-4>", self._on_scroll) # Linux scroll up
        self.text_area.bind("<Button-5>", self._on_scroll) # Linux scroll down
        self.text_area.bind("<Configure>", self._on_text_configure) # Update line numbers on resize
        self.text_area.bind("<<Modified>>", self._on_text_modified) # Update line numbers when text changes

        self._update_line_numbers() # Initial line number display

        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "JsonEditor: Editor UI built.", "DEBUG")

    # ... (rest of the class: _on_state_updated, _on_focus_requested, _on_key_release, etc.)
    def _on_state_updated(self, json_data, source=None):
        """Updates the text area when the master state changes elsewhere."""
        if source == self or not self.winfo_exists():
            return
        
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"JsonEditor: Remote state update from {source.__class__.__name__ if source else 'External'}.", "INFO")
        
        # If a specific element is focused, re-run the focus logic to get its updated data
        if hasattr(self, 'focused_path') and self.focused_path:
            self._on_focus_requested(self.focused_path, source="StateUpdate", new_state=json_data)
        else:
            # Otherwise, just show the full updated JSON
            if hasattr(self, 'text_area'):
                self.text_area.delete("1.0", "end")
                self.text_area.insert("1.0", orjson.dumps(json_data, option=orjson.OPT_INDENT_2).decode())
                self._apply_highlight()

    def _on_focus_requested(self, path, source=None, new_state=None):
        """Locates and displays the JSON for the specified path."""
        if not self.winfo_exists() or not hasattr(self, 'text_area'): return
        
        # Update the focused path
        self.focused_path = path
        
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"JsonEditor: Focus synchronization for path: {path} (Source: {source.__class__.__name__ if source else 'Unknown'})", "INFO")
        
        # If no path is provided, revert to showing the full JSON
        if not path:
            full_state = new_state or state_manager.get_state()
            self.text_area.delete("1.0", "end")
            if full_state:
                self.text_area.insert("1.0", orjson.dumps(full_state, option=orjson.OPT_INDENT_2).decode())
            self._apply_highlight()
            self._update_line_numbers()
            return

        full_state = new_state or state_manager.get_state()
        if not full_state:
            self.text_area.delete("1.0", "end")
            self._update_line_numbers()
            return

        def resolve_path(data, segments):
            curr = data
            for seg in segments:
                if isinstance(curr, dict) and seg in curr:
                    curr = curr[seg]
                elif isinstance(curr, list):
                    try:
                        idx = int(seg)
                        curr = curr[idx]
                    except (ValueError, IndexError): return None
                else:
                    return None
            return curr

        path_segments = path.split('.')
        target_data = resolve_path(full_state, path_segments)
        
        if target_data is None:
            target_data = full_state
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name, "JsonEditor: Path resolution failed. Defaulting to Root JSON.", "WARNING")

        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", orjson.dumps(target_data, option=orjson.OPT_INDENT_2).decode())
        self._apply_highlight()
        self._update_line_numbers()

    def _on_key_release(self, event):
        """Updates highlighting on key release."""
        if event.keysym not in ["Left", "Right", "Up", "Down", "Control_L", "Control_R"]:
            # logger.debug(f"JsonEditor: Key release ({event.keysym}). Updating highlights.")
            self._apply_highlight()

    def _apply_changes(self):
        """Parses the text and updates the master state_manager."""
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "JsonEditor: 'Apply Changes' manual trigger.", "INFO")
        try:
            raw_text = self.text_area.get("1.0", "end-1c")
            new_data = orjson.loads(raw_text)
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "JsonEditor: Successfully parsed JSON. Pushing to StateManager...", "SUCCESS")
            state_manager.update_state(new_data, source=self)
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "JsonEditor: Manual changes applied successfully.", "SUCCESS")
        except Exception as e:
            logger.error(f"❌ JsonEditor: JSON Syntax Error during apply: {e}")

    def _format_json(self):
        """Beautifies the JSON text."""
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "JsonEditor: 'Format JSON' manual trigger.", "INFO")
        try:
            raw_text = self.text_area.get("1.0", "end-1c")
            data = orjson.loads(raw_text)
            formatted = orjson.dumps(data, option=orjson.OPT_INDENT_2).decode()
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", formatted)
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "JsonEditor: JSON beautified. Applying highlights and syncing state_manager...", "DEBUG")
            self._apply_highlight()
            self._apply_changes()
        except Exception as e:
            logger.exception("❌ JsonEditor: Format Error")

    def _apply_highlight(self):
        """Applies basic syntax highlighting to the JSON text."""
        if not hasattr(self, 'text_area'): return
        
        # logger.debug("JsonEditor: Refreshing syntax highlighting...")
        for tag in ["key", "string", "number", "keyword"]:
            self.text_area.tag_remove(tag, "1.0", "end")
            
        content = self.text_area.get("1.0", "end-1c")
        patterns = [
            (r'"(?:\\.|[^"\\])*"(?=\s*:)', "key"),
            (r'"(?:\\.|[^"\\])*"(?!\s*:)', "string"),
            (r'\b-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b', "number"),
            (r'\b(?:true|false|null)\b', "keyword"),
        ]
        for pattern, tag in patterns:
            for match in re.finditer(pattern, content):
                start, end = match.span()
                self.text_area.tag_add(tag, f"1.0 + {start} chars", f"1.0 + {end} chars")
