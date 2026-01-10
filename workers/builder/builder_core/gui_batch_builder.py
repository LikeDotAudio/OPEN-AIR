# builder_core/gui_batch_builder.py
#
# Handles recursive JSON parsing and Grid layout.
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
import traceback
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config

app_constants = Config.get_instance()


class GuiBatchBuilderMixin:
    """Handles recursive JSON parsing and Grid layout."""

    # Recursively creates widgets in batches to prevent freezing the GUI.
    # This method processes a list of widget configurations, creating and placing them on the
    # parent frame in small batches, yielding control back to the main loop between batches.
    # Inputs:
    #     parent_frame: The parent tkinter frame to place widgets in.
    #     widget_configs (list): A list of widget configurations to process.
    #     path_prefix (str): The base path for constructing widget IDs.
    #     override_cols (int, optional): The number of columns to use for the layout.
    #     start_index (int): The starting index for the current batch.
    #     row_offset (int): The starting row for placing widgets in the grid.
    # Outputs:
    #     None.
    def _create_widgets_in_batches(
        self,
        parent_frame,
        widget_configs,
        path_prefix="",
        override_cols=None,
        start_index=0,
        row_offset=0,
    ):
        try:
            batch_size = 5
            index = start_index

            col = 0
            row = row_offset
            max_cols = int(
                self.config_data.get("layout_columns", 1)
                if override_cols is None
                else override_cols
            )

            current_data = (
                self.config_data
                if override_cols is None
                else widget_configs[start_index][1]
            )
            column_sizing = current_data.get("column_sizing", [])

            for col_idx in range(max_cols):
                sizing_info = (
                    column_sizing[col_idx] if col_idx < len(column_sizing) else {}
                )
                weight = sizing_info.get("weight", 1)
                minwidth = sizing_info.get("minwidth", 0)
                parent_frame.grid_columnconfigure(
                    col_idx, weight=weight, minsize=minwidth
                )

            # Process widgets in the current batch
            for i in range(start_index, min(start_index + batch_size, len(widget_configs))):
                key, value = widget_configs[i] # Unpack key and value for the current widget
                current_path = f"{path_prefix}/{key}".strip("/")

                if isinstance(value, dict):
                    widget_type = value.get("type")
                    layout = value.get("layout", {})
                    col_span = int(layout.get("col_span", 1))
                    row_span = int(layout.get("row_span", 1))
                    sticky = layout.get("sticky", "nsew")

                    target_frame = None

                    if widget_type == "OcaBlock":
                        show_label = value.get("show_label", True)
                        block_cols = value.get("layout_columns", None)
                        target_frame = ttk.LabelFrame(
                            parent_frame, text=key if show_label else "", borderwidth=0, relief="flat"
                        )
                        self._create_dynamic_widgets(
                            parent_frame=target_frame,
                            data=value.get("fields", {}),
                            path_prefix=current_path,
                            override_cols=block_cols,
                        )

                    elif widget_type in self.widget_factory:
                        value['path'] = current_path
                        factory_kwargs = {
                            "parent_widget": parent_frame,
                            "config_data": value,
                            "base_mqtt_topic_from_path": self.base_mqtt_topic_from_path,
                            "state_mirror_engine": self.state_mirror_engine,
                            "subscriber_router": self.subscriber_router,
                        }

                        try:
                            target_frame = self.widget_factory[widget_type](
                                **factory_kwargs
                            )
                        except Exception as e:
                            debug_logger(
                                message=f"❌ Error creating widget '{key}' of type '{widget_type}': {e}",
                                **_get_log_args(),
                            )
                            target_frame = None

                    if target_frame:
                        tk_var = self.tk_vars.get(current_path)
                        target_frame.grid(
                            row=row,
                            column=col,
                            columnspan=col_span,
                            rowspan=row_span,
                            padx=5,
                            pady=5,
                            sticky=sticky,
                        )
                        parent_frame.grid_rowconfigure(row, weight=1)
                        col += col_span
                        if col >= max_cols:
                            col = 0
                            row += row_span

            # Update index for the next batch after processing the current batch
            index = min(start_index + batch_size, len(widget_configs))

            if index < len(widget_configs):
                self.after(
                    5,
                    lambda: self._create_widgets_in_batches(
                        parent_frame,
                        widget_configs,
                        path_prefix,
                        override_cols,
                        index,
                        row,
                    ),
                )
            else:
                self._on_frame_configure()

                app_constants.PERFORMANCE_MODE = False

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message="✅ Batch processing complete! All widgets built.",
                        **_get_log_args(),
                    )

        except Exception as e:
            tb = traceback.format_exc()
            debug_logger(
                message=f"❌🔥 CRITICAL BATCH PROCESSOR FAILURE! {e}\n{tb}",
                **_get_log_args(),
            )

    # Synchronously creates and places all widgets defined in a data dictionary.
    # This method iterates through a dictionary of widget configurations and uses the
    # widget factory to create and place each widget on the parent frame.
    # Inputs:
    #     parent_frame: The parent tkinter frame.
    #     data (dict): A dictionary of widget configurations.
    #     path_prefix (str): The base path for widget IDs.
    #     override_cols (int, optional): The number of columns for the layout.
    # Outputs:
    #     None.
    def _create_dynamic_widgets(         self, parent_frame, data, path_prefix="", override_cols=None   ):
        try:
            if not isinstance(data, dict):
                return

            col = 0
            row = 0
            max_cols = int(
                data.get("layout_columns", 1)
                if override_cols is None
                else override_cols
            )
            column_sizing = data.get("column_sizing", [])

            for col_idx in range(max_cols):
                sizing_info = (
                    column_sizing[col_idx] if col_idx < len(column_sizing) else {}
                )
                weight = sizing_info.get("weight", 1)
                minwidth = sizing_info.get("minwidth", 0)
                parent_frame.grid_columnconfigure(
                    col_idx, weight=weight, minsize=minwidth
                )

            for key, value in data.items():
                current_path = f"{path_prefix}/{key}".strip("/")

                if isinstance(value, dict):
                    widget_type = value.get("type")
                    layout = value.get("layout", {})
                    col_span = int(layout.get("col_span", 1))
                    row_span = int(layout.get("row_span", 1))
                    sticky = layout.get("sticky", "nsew")

                    target_frame = None

                    if widget_type == "OcaBlock":
                        show_label = value.get("show_label", True)
                        block_cols = value.get("layout_columns", None)
                        target_frame = ttk.LabelFrame(
                            parent_frame, text=key if show_label else "", borderwidth=0, relief="flat"
                        )
                        self._create_dynamic_widgets(
                            parent_frame=target_frame,
                            data=value.get("fields", {}),
                            path_prefix=current_path,
                            override_cols=block_cols,
                        )

                    elif widget_type in self.widget_factory:
                        value['path'] = current_path
                        factory_kwargs = {
                            "parent_widget": parent_frame,
                            "config_data": value,
                            "base_mqtt_topic_from_path": self.base_mqtt_topic_from_path,
                            "state_mirror_engine": self.state_mirror_engine,
                            "subscriber_router": self.subscriber_router,
                        }
                        try:
                            target_frame = self.widget_factory[widget_type](
                                **factory_kwargs
                            )
                        except Exception as e:
                            debug_logger(
                                message=f"❌ Error creating synchronous widget '{key}' of type '{widget_type}': {e}",
                                **_get_log_args(),
                            )
                            target_frame = None

                    if target_frame:
                        tk_var = self.tk_vars.get(current_path)
                        target_frame.grid(
                            row=row,
                            column=col,
                            columnspan=col_span,
                            rowspan=row_span,
                            padx=5,
                            pady=5,
                            sticky=sticky,
                        )
                        parent_frame.grid_rowconfigure(row, weight=1)
                        col += col_span
                        if col >= max_cols:
                            col = 0
                            row += row_span       
        except Exception as e:
            debug_logger(
                message=f"❌ Error in synchronous _create_dynamic_widgets: {e}",
                **_get_log_args(),
            )