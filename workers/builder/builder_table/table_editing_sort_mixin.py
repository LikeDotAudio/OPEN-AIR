import inspect
import re
from tkinter import ttk  # For ttk.Treeview interactions

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args


class TableEditingSortMixin:
    def __init__(self):
        self._sort_column_name = None
        self._sort_reverse = False

    def _bind_headers(self):
        for col_name in self.tree["columns"]:
            self.tree.heading(col_name, command=lambda c=col_name: self._sort_column(c))
        debug_logger(message="⬆️ Binding headers for sorting.", **_get_log_args())

    def _sort_column(self, col_name):
        current_function = inspect.currentframe().f_code.co_name
        debug_logger(message=f"Sorting column: {col_name}", **_get_log_args())

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
                debug_logger(
                    message=f"Skipping row {item_id} due to column mismatch. Values: {values}",
                    level="WARNING",
                    **_get_log_args(),
                )

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

        debug_logger(
            message=f"Column '{col_name}' sorted {'descending' if self._sort_reverse else 'ascending'}.",
            **_get_log_args(),
        )
