
import inspect

# FileReaders/editor.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized Importer Editor Logic.
# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

from oaFileHandlers.oaFileImportShow.FileReaders.saver import save_markers_file_internally

from .Core.string_utils import StringUtils

# --- EXTRACTED CORE MODULES ---
from .Core.tree_cell_editor import TreeCellEditor
from .Core.tree_navigation_engine import TreeNavigationEngine
from .Core.tree_sorting_engine import TreeSortingEngine


def on_tree_double_click(tab, event):
    """Handles double-click to initiate cell editing."""
    if not tab.marker_tree.identify_region(event.x, event.y) == "cell": return
    cid = tab.marker_tree.identify_column(event.x); iid = tab.marker_tree.identify_row(event.y)
    if not iid or not cid: return
    idx = int(cid[1:]) - 1
    if idx < 0 or idx >= len(tab.tree_headers): return

    value = tab.marker_tree.item(iid, "values")[idx]
    start_editing_cell(tab, iid, idx, initial_value=value)

def start_editing_cell(tab, item, col_idx, initial_value=""):
    """Spawns the in-place editor and sets up navigation callbacks."""
    def nav_cb(it, ci, d): navigate_cells(tab, it, ci, d)
    TreeCellEditor.start(tab, item, col_idx, initial_value, nav_cb)

def navigate_cells(tab, item, col_idx, direction):
    """Orchestrates editor movement across the treeview grid."""
    def start_cb(it, ci, iv): start_editing_cell(tab, it, ci, iv)
    TreeNavigationEngine.navigate(tab, item, col_idx, direction, start_cb)

def increment_string_with_trailing_digits(text):
    """Backwards compatibility wrapper for StringUtils."""
    return StringUtils.increment_trailing_digits(text)

def on_tree_header_click(tab, event):
    """Handles header clicks to trigger column sorting."""
    if tab.marker_tree.identify_region(event.x, event.y) == "heading":
        cid = tab.marker_tree.identify_column(event.x); idx = int(cid[1:]) - 1
        if idx < 0 or idx >= len(tab.tree_headers): return

        name = tab.tree_headers[idx]
        if tab.sort_column == name: tab.sort_direction = not tab.sort_direction
        else: tab.sort_column, tab.sort_direction = name, True
        sort_treeview(tab, name, tab.sort_direction)

def sort_treeview(tab, column_name, ascending):
    """Sorts the data model and refreshes the display."""
    TreeSortingEngine.sort(tab.tree_data, column_name, ascending)
    populate_marker_tree(tab)
    matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"✅ Sorted by '{column_name}' {'Asc' if ascending else 'Desc'}", "SUCCESS")

def populate_marker_tree(tab):
    """Re-populates the treeview from the internal data model."""
    tab.marker_tree.delete(*tab.marker_tree.get_children())
    hdrs = tab.tree_headers if tab.tree_headers else ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]
    tab.marker_tree["columns"] = hdrs
    for col in hdrs:
        tab.marker_tree.heading(col, text=col, command=lambda c=col: sort_treeview(tab, c, tab.sort_column != c or not tab.sort_direction))
        tab.marker_tree.column(col, width=100)
    for row in tab.tree_data:
        vals = [row.get(h, "") for h in hdrs]
        tab.marker_tree.insert("", "end", values=vals)

def delete_selected_row(tab, event):
    """Deletes selected rows and syncs with storage."""
    sel = tab.marker_tree.selection()
    if not sel: return
    for item in sel:
        idx = tab.marker_tree.index(item)
        if idx < len(tab.tree_data):
            tab.marker_tree.delete(item); del tab.tree_data[idx]
            matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"✅ Deleted row {idx+1}", "SUCCESS")
    save_markers_file_internally(tab)
