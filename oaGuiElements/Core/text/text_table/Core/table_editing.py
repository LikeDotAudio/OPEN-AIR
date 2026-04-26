# text_table/table_editing.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: text_table/table_editing_manager.py

import inspect

# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

from .table_editing_inplace_mixin import TableEditingInplaceMixin
from .table_editing_row_ops_mixin import TableEditingRowOpsMixin
from .table_editing_sort_mixin import TableEditingSortMixin
from .table_editing_undo_mixin import TableEditingUndoMixin


class TableEditingManager(
    TableEditingInplaceMixin,
    TableEditingUndoMixin,
    TableEditingRowOpsMixin,
    TableEditingSortMixin,
):
    # Initializes the TableEditingManager.
    # This constructor sets up the Treeview widget with all the editing, undo,
    # row operation, and sorting functionalities provided by its mixins. It also
    # binds relevant events and initializes state for managing table data.
    # Inputs:
    #     tree: The Tkinter Treeview widget to manage.
    #     state_mirror_engine: The state mirror engine for MQTT synchronization.
    #     data_topic (str): The base MQTT topic for this table's data.
    #     allow_sort (bool): Whether to allow column sorting.
    #     allow_undo (bool): Whether to allow undo operations.
    #     allow_delete (bool): Whether to allow row deletion.
    # Outputs:
    #     None.
    def __init__(self, tree, state_mirror_engine, data_topic, allow_sort=True, allow_undo=True, allow_delete=True):
        # Initialize mixins
        TableEditingInplaceMixin.__init__(self)
        TableEditingUndoMixin.__init__(self)
        TableEditingRowOpsMixin.__init__(self)
        TableEditingSortMixin.__init__(self)

        self.tree = tree
        self.state_mirror_engine = state_mirror_engine
        self.data_topic = data_topic

        # Bindings specific to TableEditingManager (which are now methods of mixins)
        self.tree.bind("<Double-1>", self.on_double_click)

        if allow_delete:
            self.tree.bind("<Delete>", self.delete_selection)

        if allow_undo:
            self.tree.bind("<Control-z>", self.undo)

        # Setup Header Sorting (method from TableEditingSortMixin)
        if allow_sort:
            self._bind_headers()

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📊 TableEditingManager initialized for tree {tree}", level="DEBUG")
