import tkinter as tk
from tkinter import ttk
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
import orjson
import inspect
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.mqtt import mqtt_publisher_service
from .table_editing_inplace_mixin import TableEditingInplaceMixin
from .table_editing_undo_mixin import TableEditingUndoMixin
from .table_editing_row_ops_mixin import TableEditingRowOpsMixin
from .table_editing_sort_mixin import TableEditingSortMixin


class TableEditingManager(
    TableEditingInplaceMixin,
    TableEditingUndoMixin,
    TableEditingRowOpsMixin,
    TableEditingSortMixin,
):
    def __init__(self, tree, state_mirror_engine, data_topic):
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
        self.tree.bind("<Delete>", self.delete_selection)
        self.tree.bind("<Control-z>", self.undo)

        # Setup Header Sorting (method from TableEditingSortMixin)
        self._bind_headers()

        debug_logger(
            message=f"📊 TableEditingManager initialized for tree {tree}",
            **_get_log_args(),
        )
