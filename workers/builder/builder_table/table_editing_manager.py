# builder_table/table_editing_manager.py
#
# This module defines the TableEditingManager, which combines multiple mixins to provide comprehensive editing, undo, and sorting functionalities for Treeview widgets.
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
    # Initializes the TableEditingManager.
    # This constructor sets up the Treeview widget with all the editing, undo,
    # row operation, and sorting functionalities provided by its mixins. It also
    # binds relevant events and initializes state for managing table data.
    # Inputs:
    #     tree: The Tkinter Treeview widget to manage.
    #     state_mirror_engine: The state mirror engine for MQTT synchronization.
    #     data_topic (str): The base MQTT topic for this table's data.
    # Outputs:
    #     None.
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