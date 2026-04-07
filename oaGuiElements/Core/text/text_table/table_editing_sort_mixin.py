# text_table/table_editing_sort_mixin.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: text_table/table_editing_sort_mixin.py

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import re

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import TABLE_LOGGER
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()


class TableEditingSortMixin:
    # Initializes the TableEditingSortMixin.
    # This sets up internal state variables to track the currently sorted column and its order.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def __init__(self):
        self._sort_column_name = None
        self._sort_reverse = False

    # Binds the sort functionality to each column header of the Treeview.
    # This method iterates through all defined columns in the Treeview and associates
    # a click command with each header to trigger sorting for that column.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def _bind_headers(self):
        for col_name in self.tree["columns"]:
            self.tree.heading(col_name, command=lambda c=col_name: self._sort_column(c))
        matrix_log("ui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Binding headers for sorting.", "DEBUG")

    # Sorts the Treeview data based on the specified column.
    # This method retrieves all data from the Treeview, sorts it based on the values
    # in the target column (handling both numeric and string types), and then
    # rearranges the items in the Treeview to reflect the new order.
    # Inputs:
    #     col_name (str): The name of the column to sort by.
    # Outputs:
    #     None.
    def _sort_column(self, col_name):
        matrix_log("ui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Sorting column: {col_name}", "DEBUG")

        # Get all items in the Treeview
        data = []
        for item_id in self.tree.get_children(""):
            values = self.tree.item(item_id, "values")
            # Ensure the number of values matches columns
            if len(values) == len(self.tree["columns"]):
                # Create a dictionary for easier access by column name
                row_dict = {
                    self.tree["columns"][i]: values[i] for i in range(len(values))
                }
                data.append((item_id, row_dict))
            else:
                TABLE_LOGGER.warning(f"Skipping row {item_id} due to column mismatch. Values: {values}")

        if not data:
            return

        # Determine sort order
        if col_name == self._sort_column_name:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column_name = col_name
            self._sort_reverse = False  # Default to ascending for new column

        # Sort the data
        # Use a more robust key function that handles mixed types (e.g., numbers vs strings)
        def get_sort_key(item_tuple):
            row_dict = item_tuple[1]
            value = row_dict.get(col_name, "")
            try:
                # Try to convert to float for numeric sorting
                return float(value)
            except (ValueError, TypeError):
                # Fallback to string for non-numeric values
                return str(value).lower()

        data.sort(key=get_sort_key, reverse=self._sort_reverse)

        # Rearrange items in the Treeview
        for index, (item_id, _) in enumerate(data):
            self.tree.move(item_id, "", index)

        # Update header arrow to indicate sort order
        # For now, just use text indicators, as images require more setup
        for c in self.tree["columns"]:
            if c == col_name:
                self.tree.heading(c, text=f"{c}{' ▼' if self._sort_reverse else ' ▲'}")
            else:
                # Remove arrow from other columns
                original_text = self.tree.heading(c, "text")
                self.tree.heading(c, text=re.sub(r" [▼▲]", "", original_text))

        matrix_log("ui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Column '{col_name}' sorted {'descending' if self._sort_reverse else 'ascending'}.", "DEBUG")