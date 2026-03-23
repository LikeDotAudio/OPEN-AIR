# workspaces/json_editor.py
# Author: Gemini CLI
# Version: 1.0.0
#
# Description: The Code-level JSON Editor Workspace.

import tkinter as tk
from tkinter import ttk
import orjson
import re
from ..event_bus import event_bus
from ..state import state_manager

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import GUI_LOGGER as logger


class JsonEditor(tk.Frame):
    """The workspace for manual JSON editing with syntax highlighting."""

    def __init__(self, parent, *args, **kwargs):
        kwargs.pop("bg", None)
        super().__init__(parent, bg="#1e1e1e", *args, **kwargs)
        if LOCAL_DEBUG: logger.debug("JsonEditor: Initializing workspace...")
        self._build_ui()
        
        # Subscribe to state updates
        if LOCAL_DEBUG: logger.debug("JsonEditor: Subscribing to EventBus...")
        event_bus.subscribe("STATE_UPDATED", self._on_state_updated)
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)
        
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event):
        """Unsubscribe from event bus when widget is destroyed."""
        if event.widget == self:
            if LOCAL_DEBUG: logger.info("JsonEditor: Workspace destroyed. Cleaning up subscriptions.")
            event_bus.unsubscribe("STATE_UPDATED", self._on_state_updated)
            event_bus.unsubscribe("FOCUS_REQUESTED", self._on_focus_requested)

    def _build_ui(self):
        """Builds the JSON editor UI."""
        if LOCAL_DEBUG: logger.debug("JsonEditor: Creating Editor UI components...")
        header = tk.Frame(self, bg="#333333", height=35)
        header.pack(side="top", fill="x")
        
        tk.Label(header, text="JSON DEFINITION EDITOR", bg="#333333", fg="white", 
                 font=("Arial", 9, "bold")).pack(side="left", padx=10, pady=5)
        
        ttk.Button(header, text="Apply Changes", command=self._apply_changes).pack(side="right", padx=5)
        ttk.Button(header, text="Format JSON", command=self._format_json).pack(side="right", padx=5)

        # Editor area with scrollbar
        self.text_area = tk.Text(self, bg="#1e1e1e", fg="#dcdcdc", insertbackground="white",
                                 font=("Consolas", 11), wrap="none", undo=True, bd=0)
        self.text_area.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text_area.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_area.config(yscrollcommand=scrollbar.set)
        
        # Configure highlighting tags
        self.text_area.tag_configure("key", foreground="#9cdcfe")
        self.text_area.tag_configure("string", foreground="#ce9178")
        self.text_area.tag_configure("number", foreground="#b5cea8")
        self.text_area.tag_configure("keyword", foreground="#569cd6")
        self.text_area.tag_configure("search_highlight", background="#444400")

        self.text_area.bind("<KeyRelease>", self._on_key_release)
        if LOCAL_DEBUG: logger.debug("JsonEditor: Editor UI built.")

    def _on_state_updated(self, json_data, source=None):
        """Updates the text area when the master state changes elsewhere."""
        if source == self or not self.winfo_exists():
            return
        
        if LOCAL_DEBUG: logger.info(f"JsonEditor: Remote state update from {source.__class__.__name__ if source else 'External'}. Syncing text area.")
        # Check if text_area exists (should be true if _build_ui finished)
        if hasattr(self, 'text_area'):
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", orjson.dumps(json_data, option=orjson.OPT_INDENT_2).decode())
            if LOCAL_DEBUG: logger.debug("JsonEditor: Applying syntax highlighting after sync...")
            self._apply_highlight()

    def _on_focus_requested(self, path, source=None):
        """Locates and highlights the specified path in the JSON text."""
        if not path or not self.winfo_exists() or not hasattr(self, 'text_area'): return
        
        if LOCAL_DEBUG: logger.info(f"JsonEditor: Focus synchronization for path: {path} (Source: {source.__class__.__name__ if source else 'Unknown'})")
        # Convert dot-path to last key for simple text search
        search_key = f'"{path.split(".")[-1]}"'
        
        pos = self.text_area.search(search_key, "1.0", stopindex="end")
        if pos:
            if LOCAL_DEBUG: logger.debug(f"JsonEditor: Found search key '{search_key}' at position {pos}. Highlighting line.")
            self.text_area.tag_remove("search_highlight", "1.0", "end")
            self.text_area.tag_add("search_highlight", f"{pos} linestart", f"{pos} lineend")
            self.text_area.see(pos)
            self.text_area.mark_set("insert", pos)
            self.text_area.focus_set()
        else:
             if LOCAL_DEBUG: logger.debug(f"JsonEditor: Search key '{search_key}' NOT FOUND in text area.")

    def _on_key_release(self, event):
        """Updates highlighting on key release."""
        if event.keysym not in ["Left", "Right", "Up", "Down", "Control_L", "Control_R"]:
            # logger.debug(f"JsonEditor: Key release ({event.keysym}). Updating highlights.")
            self._apply_highlight()

    def _apply_changes(self):
        """Parses the text and updates the master state_manager."""
        if LOCAL_DEBUG: logger.info("JsonEditor: 'Apply Changes' manual trigger.")
        try:
            raw_text = self.text_area.get("1.0", "end-1c")
            new_data = orjson.loads(raw_text)
            if LOCAL_DEBUG: logger.success("JsonEditor: Successfully parsed JSON. Pushing to StateManager...")
            state_manager.update_state(new_data, source=self)
            if LOCAL_DEBUG: logger.success("JsonEditor: Manual changes applied successfully.")
        except Exception as e:
            logger.error(f"❌ JsonEditor: JSON Syntax Error during apply: {e}")

    def _format_json(self):
        """Beautifies the JSON text."""
        if LOCAL_DEBUG: logger.info("JsonEditor: 'Format JSON' manual trigger.")
        try:
            raw_text = self.text_area.get("1.0", "end-1c")
            data = orjson.loads(raw_text)
            formatted = orjson.dumps(data, option=orjson.OPT_INDENT_2).decode()
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", formatted)
            if LOCAL_DEBUG: logger.debug("JsonEditor: JSON beautified. Applying highlights and syncing state_manager...")
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
