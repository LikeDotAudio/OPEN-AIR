# importers/worker_importer_editor.py
#
# This module provides functions for in-place editing, navigation, and deletion of rows in a Tkinter Treeview widget for marker data.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1

import inspect
import os
import re
import tkinter as tk
from tkinter import ttk
from workers.logger.debug_logger import debug_logger
from workers.importers.worker_importer_saver import save_markers_file_internally

LOCAL_DEBUG_ENABLE = False


# Handles a double-click event on the Treeview to initiate cell editing.
# This function identifies the cell that was double-clicked and calls `start_editing_cell`
# to spawn an Entry widget over it, allowing the user to modify the cell's content.
# Inputs:
#     importer_tab_instance: The instance of the importer tab containing the Treeview.
#     event: The tkinter double-click event object.
# Outputs:
#     None.
def on_tree_double_click(importer_tab_instance, event):
    current_function = inspect.currentframe().f_code.co_name
    current_file = os.path.basename(__file__)
    debug_logger(
        message=f"▶️ Treeview double-clicked for editing.",
        file=current_file,
        version=current_version,
        function=current_function,
    )
    if (
        not importer_tab_instance.marker_tree.identify_region(event.x, event.y)
        == "cell"
    ):
        return
    column_id = importer_tab_instance.marker_tree.identify_column(event.x)
    item_id = importer_tab_instance.marker_tree.identify_row(event.y)
    if not item_id or not column_id:
        return
    col_index = int(column_id[1:]) - 1
    if col_index < 0 or col_index >= len(importer_tab_instance.tree_headers):
        debug_logger(
            message=f"⚠️ Invalid column index {col_index} for editing.",
            file=current_file,
            version=current_version,
            function=current_function,
        )
        return
    current_value = importer_tab_instance.marker_tree.item(item_id, "values")[col_index]
    start_editing_cell(
        importer_tab_instance, item_id, col_index, initial_value=current_value
    )


# Starts an in-place editing session for a specified cell in the Treeview.
# This function creates and places an Entry widget over the target cell, pre-populates it
# with the cell's current value, and binds events for committing or canceling the edit,
# including navigation to other cells.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
#     item: The ID of the Treeview item (row).
#     col_index (int): The index of the column to edit.
#     initial_value (str): The initial value to display in the editor.
# Outputs:
#     None.
def start_editing_cell(importer_tab_instance, item, col_index, initial_value=""):
    current_function = inspect.currentframe().f_code.co_name
    current_file = os.path.basename(__file__)
    for widget in importer_tab_instance.marker_tree.winfo_children():
        if isinstance(widget, ttk.Entry) and widget.winfo_name() == "cell_editor":
            widget.destroy()
    entry_editor = ttk.Entry(
        importer_tab_instance.marker_tree, style="Markers.TEntry", name="cell_editor"
    )
    entry_editor.insert(0, initial_value)
    entry_editor.focus_force()
    x, y, width, height = importer_tab_instance.marker_tree.bbox(
        item, importer_tab_instance.marker_tree["columns"][col_index]
    )
    entry_editor.place(x=x, y=y, width=width, height=height)
    entry_editor.current_item = item
    entry_editor.current_col_index = col_index

    def on_edit_complete_and_navigate(event, navigate_direction=None):
        new_value = entry_editor.get()
        entry_editor.destroy()
        current_values = list(importer_tab_instance.marker_tree.item(item, "values"))
        current_values[col_index] = new_value
        importer_tab_instance.marker_tree.item(item, values=current_values)
        row_idx = importer_tab_instance.marker_tree.index(item)
        if row_idx < len(importer_tab_instance.tree_data) and isinstance(
            importer_tab_instance.tree_data[row_idx], dict
        ):
            importer_tab_instance.tree_data[row_idx][
                importer_tab_instance.tree_headers[col_index]
            ] = new_value
            debug_logger(
                message=f"✅ Updated cell: Row {row_idx+1}, Column '{importer_tab_instance.tree_headers[col_index]}' to '{new_value}'"
            )
            save_markers_file_internally(importer_tab_instance)
        else:
            debug_logger(
                message=f"❌ Error: Row index {row_idx} out of bounds or data not a dictionary for self.tree_data.",
                file=current_file,
                version=current_version,
                function=current_function,
            )
        if navigate_direction:
            navigate_cells(importer_tab_instance, item, col_index, navigate_direction)

    entry_editor.bind("<Return>", lambda e: on_edit_complete_and_navigate(e, "down"))
    entry_editor.bind("<Tab>", lambda e: on_edit_complete_and_navigate(e, "right"))
    entry_editor.bind("<Shift-Tab>", lambda e: on_edit_complete_and_navigate(e, "left"))
    entry_editor.bind(
        "<Control-Return>", lambda e: on_edit_complete_and_navigate(e, "ctrl_down")
    )
    entry_editor.bind("<FocusOut>", lambda e: on_edit_complete_and_navigate(e, None))
    entry_editor.bind("<Up>", lambda e: on_edit_complete_and_navigate(e, "up"))
    entry_editor.bind("<Down>", lambda e: on_edit_complete_and_navigate(e, "down"))
    entry_editor.bind("<Left>", lambda e: on_edit_complete_and_navigate(e, "left"))
    entry_editor.bind("<Right>", lambda e: on_edit_complete_and_navigate(e, "right"))


# Navigates to an adjacent cell in the Treeview after an edit or a navigation command.
# This function calculates the next row and column index based on the direction,
# updates the Treeview selection, and initiates editing for the new cell.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
#     current_item: The ID of the currently active Treeview item.
#     current_col_index (int): The index of the currently active column.
#     direction (str): The navigation direction ('up', 'down', 'left', 'right', 'ctrl_down').
# Outputs:
#     None.
def navigate_cells(importer_tab_instance, current_item, current_col_index, direction):
    current_function = inspect.currentframe().f_code.co_name
    current_file = os.path.basename(__file__)
    debug_logger(
        message=f"▶️ Navigating cells.",
        file=current_file,
        version=current_version,
        function=current_function,
    )
    items = importer_tab_instance.marker_tree.get_children()
    num_rows = len(items)
    num_cols = len(importer_tab_instance.tree_headers)
    current_row_idx = items.index(current_item) if current_item in items else -1
    next_item = None
    next_col_index = -1
    initial_value_for_next_cell = ""
    if current_row_idx == -1:
        debug_logger(
            message=f"🟡 Current item not found in tree for navigation.",
            file=current_file,
            version=current_version,
            function=current_function,
        )
        return
    if direction == "down":
        next_row_idx = current_row_idx + 1
        next_col_index = current_col_index
        if next_row_idx < num_rows:
            next_item = items[next_row_idx]
    elif direction == "up":
        next_row_idx = current_row_idx - 1
        next_col_index = current_col_index
        if next_row_idx >= 0:
            next_item = items[next_row_idx]
    elif direction == "right":
        next_col_index = current_col_index + 1
        if next_col_index < num_cols:
            next_item = current_item
        else:
            next_row_idx = current_row_idx + 1
            if next_row_idx < num_rows:
                next_item = items[next_row_idx]
                next_col_index = 0
    elif direction == "left":
        next_col_index = current_col_index - 1
        if next_col_index >= 0:
            next_item = current_item
        else:
            next_row_idx = current_row_idx - 1
            if next_row_idx >= 0:
                next_item = items[next_row_idx]
                next_col_index = num_cols - 1
    elif direction == "ctrl_down":
        next_row_idx = current_row_idx + 1
        next_col_index = current_col_index
        if next_row_idx < num_rows:
            next_item = items[next_row_idx]
            prev_cell_value = importer_tab_instance.marker_tree.item(
                current_item, "values"
            )[current_col_index]
            initial_value_for_next_cell = increment_string_with_trailing_digits(
                prev_cell_value
            )
            new_values = list(
                importer_tab_instance.marker_tree.item(next_item, "values")
            )
            new_values[next_col_index] = initial_value_for_next_cell
            importer_tab_instance.marker_tree.item(next_item, values=new_values)
            if next_row_idx < len(importer_tab_instance.tree_data) and isinstance(
                importer_tab_instance.tree_data[next_row_idx], dict
            ):
                importer_tab_instance.tree_data[next_row_idx][
                    importer_tab_instance.tree_headers[next_col_index]
                ] = initial_value_for_next_cell
            else:
                debug_logger(
                    message=f"🟡 Cannot Ctrl+Enter: No row below.",
                    file=current_file,
                    version=current_version,
                    function=current_function,
                )
                return
    if next_item is not None and next_col_index != -1:
        if direction != "ctrl_down":
            try:
                next_item_values = importer_tab_instance.marker_tree.item(
                    next_item, "values"
                )
                if 0 <= next_col_index < len(next_item_values):
                    initial_value_for_next_cell = next_item_values[next_col_index]
                else:
                    debug_logger(
                        message=f"🟡 Next column index {next_col_index} out of bounds for next item values. Setting empty.",
                        file=current_file,
                        version=current_version,
                        function=current_function,
                    )
                    initial_value_for_next_cell = ""
            except Exception as e:
                debug_logger(
                    message=f"❌ Error getting initial value for next cell: {e}. Setting empty.",
                    file=current_file,
                    version=current_version,
                    function=current_function,
                )
                initial_value_for_next_cell = ""
        importer_tab_instance.marker_tree.focus(next_item)
        importer_tab_instance.marker_tree.selection_set(next_item)
        importer_tab_instance.after(
            10,
            lambda: start_editing_cell(
                importer_tab_instance,
                next_item,
                next_col_index,
                initial_value_for_next_cell,
            ),
        )
    else:
        debug_logger(
            message=f"🟡 No cell to navigate to in direction: {direction}",
            file=current_file,
            version=current_version,
            function=current_function,
        )


# Increments any trailing digits found in a string.
# This utility function is used for auto-incrementing cell values. If the string
# ends with numbers, it increments them; otherwise, it returns the original string.
# Inputs:
#     text (str): The input string.
# Outputs:
#     str: The string with incremented trailing digits.
def increment_string_with_trailing_digits(text):
    match = re.search(r"(\d+)$", text)
    if match:
        num_str = match.group(1)
        num_int = int(num_str)
        incremented_num = num_int + 1
        new_num_str = str(incremented_num).zfill(len(num_str))
        return text[: -len(num_str)] + new_num_str
    return text


# Handles a click event on a Treeview column header to trigger sorting.
# This function identifies the clicked column, updates the sort column and direction,
# and then calls `sort_treeview` to reorder the table display.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
#     event: The tkinter event object (from a header click).
# Outputs:
#     None.
def on_tree_header_click(importer_tab_instance, event):
    current_function = inspect.currentframe().f_code.co_name
    current_file = os.path.basename(__file__)
    debug_logger(
        message=f"▶️ Treeview header clicked for sorting.",
        file=current_file,
        version=current_version,
        function=current_function,
    )
    region = importer_tab_instance.marker_tree.identify_region(event.x, event.y)
    if region == "heading":
        column_id = importer_tab_instance.marker_tree.identify_column(event.x)
        col_index = int(column_id[1:]) - 1
        if col_index < 0 or col_index >= len(importer_tab_instance.tree_headers):
            debug_logger(
                message=f"⚠️ Invalid column index {col_index} for sorting.",
                file=current_file,
                version=current_version,
                function=current_function,
            )
            return
        column_name = importer_tab_instance.tree_headers[col_index]
        if importer_tab_instance.sort_column == column_name:
            importer_tab_instance.sort_direction = (
                not importer_tab_instance.sort_direction
            )
        else:
            importer_tab_instance.sort_column = column_name
            importer_tab_instance.sort_direction = True
        sort_treeview(
            importer_tab_instance, column_name, importer_tab_instance.sort_direction
        )


# Sorts the Treeview data based on the specified column and direction.
# This function extracts data from the Treeview, sorts the internal data model,
# and then re-populates the Treeview to reflect the sorted order.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
#     column_name (str): The name of the column to sort by.
#     ascending (bool): True for ascending order, False for descending.
# Outputs:
#     None.
def sort_treeview(importer_tab_instance, column_name, ascending):
    current_function = inspect.currentframe().f_code.co_name
    current_file = os.path.basename(__file__)
    debug_logger(
        message=f"▶️ Sorting treeview by '{column_name}', ascending: {ascending}.",
        file=current_file,
        version=current_version,
        function=current_function,
    )

    def get_sort_key(item):
        value = item.get(column_name, "")
        try:
            return float(value)
        except (ValueError, TypeError):
            return str(value)

    importer_tab_instance.tree_data.sort(key=get_sort_key, reverse=not ascending)
    populate_marker_tree(importer_tab_instance)
    debug_logger(
        message=f"✅ Sorted by '{column_name}' {'Ascending' if ascending else 'Descending'}."
    )


# Re-populates the Treeview from the internal data model.
# This function clears all existing items in the Treeview, updates the column headers
# (if necessary), and then inserts rows from the internal `tree_data` list.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
# Outputs:
#     None.
def populate_marker_tree(importer_tab_instance):
    """Re-populates the treeview from the internal data model."""
    importer_tab_instance.marker_tree.delete(
        *importer_tab_instance.marker_tree.get_children()
    )
    standardized_headers = (
        importer_tab_instance.tree_headers
        if importer_tab_instance.tree_headers
        else ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]
    )
    importer_tab_instance.marker_tree["columns"] = standardized_headers
    for col in standardized_headers:
        importer_tab_instance.marker_tree.heading(
            col,
            text=col,
            command=lambda c=col: sort_treeview(
                importer_tab_instance,
                c,
                importer_tab_instance.sort_column != c
                or not importer_tab_instance.sort_direction,
            ),
        )
        importer_tab_instance.marker_tree.column(col, width=100)
    for row in importer_tab_instance.tree_data:
        values = [row.get(raw_header, "") for raw_header in standardized_headers]
        importer_tab_instance.marker_tree.insert("", "end", values=values)


# Deletes the currently selected rows from the Treeview and the internal data model.
# This function removes the selected items from the Treeview widget and also
# deletes the corresponding data entries from the `tree_data` list.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
#     event: The tkinter event object (e.g., from a Delete key press).
# Outputs:
#     None.
def delete_selected_row(importer_tab_instance, event):
    current_function = inspect.currentframe().f_code.co_name
    debug_logger(
        message=f"▶️ Delete key pressed.",
        file=importer_tab_instance.current_file,
        version=importer_tab_instance.current_version,
        function=current_function,
    )
    selected_items = importer_tab_instance.marker_tree.selection()
    if not selected_items:
        debug_logger(message="🟡 No row selected to delete.")
        return
    for item in selected_items:
        index_in_tree = importer_tab_instance.marker_tree.index(item)
        if index_in_tree < len(importer_tab_instance.tree_data):
            importer_tab_instance.marker_tree.delete(item)
            del importer_tab_instance.tree_data[index_in_tree]
            debug_logger(message=f"✅ Deleted row {index_in_tree + 1}.")
        else:
            debug_logger(
                message=f"❌ Error: Row {index_in_tree + 1} not found in data."
            )
    save_markers_file_internally(importer_tab_instance)