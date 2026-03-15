from loguru import logger
from .string_utils import StringUtils

class TreeNavigationEngine:
    """Handles the coordinate and logic mapping for moving the active cell editor."""

    @staticmethod
    def navigate(tab, cur_item, cur_col, direction, start_editor_cb):
        items = tab.marker_tree.get_children()
        num_rows, num_cols = len(items), len(tab.tree_headers)
        row_idx = items.index(cur_item) if cur_item in items else -1
        if row_idx == -1: return

        nxt_item, nxt_col, init_val = None, -1, ""

        if direction == "down":
            if row_idx + 1 < num_rows: nxt_item, nxt_col = items[row_idx + 1], cur_col
        elif direction == "up":
            if row_idx - 1 >= 0: nxt_item, nxt_col = items[row_idx - 1], cur_col
        elif direction == "right":
            if cur_col + 1 < num_cols: nxt_item, nxt_col = cur_item, cur_col + 1
            elif row_idx + 1 < num_rows: nxt_item, nxt_col = items[row_idx + 1], 0
        elif direction == "left":
            if cur_col - 1 >= 0: nxt_item, nxt_col = cur_item, cur_col - 1
            elif row_idx - 1 >= 0: nxt_item, nxt_col = items[row_idx - 1], num_cols - 1
        elif direction == "ctrl_down":
            if row_idx + 1 < num_rows:
                nxt_item, nxt_col = items[row_idx + 1], cur_col
                prev_val = tab.marker_tree.item(cur_item, "values")[cur_col]
                init_val = StringUtils.increment_trailing_digits(prev_val)
                # Apply immediately for Ctrl+Down
                vals = list(tab.marker_tree.item(nxt_item, "values"))
                vals[nxt_col] = init_val
                tab.marker_tree.item(nxt_item, values=vals)
                if row_idx + 1 < len(tab.tree_data):
                    tab.tree_data[row_idx + 1][tab.tree_headers[nxt_col]] = init_val

        if nxt_item and nxt_col != -1:
            if direction != "ctrl_down":
                init_val = tab.marker_tree.item(nxt_item, "values")[nxt_col]
            
            tab.marker_tree.focus(nxt_item); tab.marker_tree.selection_set(nxt_item)
            tab.after(10, lambda: start_editor_cb(nxt_item, nxt_col, init_val))
