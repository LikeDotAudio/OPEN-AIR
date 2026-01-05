import tkinter as tk
from tkinter import ttk
import traceback
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config

app_constants = Config.get_instance()


class GuiBatchBuilderMixin:
    """Handles recursive JSON parsing and Grid layout."""

    def _create_widgets_in_batches(self, parent_frame, widget_configs, path_prefix="", override_cols=None, start_index=0, row_offset=0):
        try:
            batch_size = 5
            index = start_index

            col = 0
            row = row_offset
            max_cols = int(self.config_data.get("layout_columns", 1) if override_cols is None else override_cols)

            current_data = self.config_data if override_cols is None else widget_configs[start_index][1]
            column_sizing = current_data.get("column_sizing", [])

            for col_idx in range(max_cols):
                sizing_info = column_sizing[col_idx] if col_idx < len(column_sizing) else {}
                weight = sizing_info.get("weight", 1)
                minwidth = sizing_info.get("minwidth", 0)
                parent_frame.grid_columnconfigure(col_idx, weight=weight, minsize=minwidth)

            while index < len(widget_configs) and index < start_index + batch_size:
                key, value = widget_configs[index]
                current_path = f"{path_prefix}/{key}".strip("/")

                if isinstance(value, dict):
                    widget_type = value.get("type")
                    layout = value.get("layout", {})
                    col_span = int(layout.get("col_span", 1))
                    row_span = int(layout.get("row_span", 1))
                    sticky = layout.get("sticky", "nsew")

                    target_frame = None

                    if widget_type == "OcaBlock":
                        block_cols = value.get("layout_columns", None)
                        target_frame = ttk.LabelFrame(parent_frame, text=key, borderwidth=0, relief="flat")
                        self._create_dynamic_widgets(parent_frame=target_frame, data=value.get("fields", {}), path_prefix=current_path, override_cols=block_cols)

                    elif widget_type in self.widget_factory:
                        # Inject global context into the widget's config_data
                        value["path"] = current_path # Inject current widget's path
                        if self.state_mirror_engine:
                            value["state_mirror_engine"] = self.state_mirror_engine
                            value["base_mqtt_topic_from_path"] = self.state_mirror_engine.base_topic
                        if self.subscriber_router:
                            value["subscriber_router"] = self.subscriber_router

                        factory_kwargs = {
                            "parent_widget": parent_frame,
                            "config_data": value # Pass the modified config_data
                        }

                        try:
                            target_frame = self.widget_factory[widget_type](**factory_kwargs)
                        except Exception as e:
                            debug_logger(message=f"❌ Error creating widget '{key}' of type '{widget_type}': {e}", **_get_log_args())
                            target_frame = None
                    else:
                        debug_logger(message=f"❓ Unknown or missing widget 'type' for widget '{key}'. Skipping.", **_get_log_args())

                    if target_frame:
                        tk_var = self.tk_vars.get(current_path)
                        target_frame.grid(row=row, column=col, columnspan=col_span, rowspan=row_span, padx=5, pady=5, sticky=sticky)
                        parent_frame.grid_rowconfigure(row, weight=1)
                        col += col_span
                        if col >= max_cols:
                            col = 0
                            row += row_span

                index += 1

            if index < len(widget_configs):
                self.after(5, lambda: self._create_widgets_in_batches(parent_frame, widget_configs, path_prefix, override_cols, index, row))
            else:
                self._on_frame_configure()

                app_constants.PERFORMANCE_MODE = False

                if app_constants.global_settings['debug_enabled']:
                    debug_logger(message="✅ Batch processing complete! All widgets built.", **_get_log_args())

        except Exception as e:
            tb = traceback.format_exc()
            debug_logger(message=f"❌🔥 CRITICAL BATCH PROCESSOR FAILURE! {e}\n{tb}", **_get_log_args())
        
    def _create_dynamic_widgets(self, parent_frame, data, path_prefix="", override_cols=None):
        try:
            if not isinstance(data, dict):
                return

            col = 0
            row = 0
            max_cols = int(data.get("layout_columns", 1) if override_cols is None else override_cols)
            column_sizing = data.get("column_sizing", [])

            for col_idx in range(max_cols):
                sizing_info = column_sizing[col_idx] if col_idx < len(column_sizing) else {}
                weight = sizing_info.get("weight", 1)
                minwidth = sizing_info.get("minwidth", 0)
                parent_frame.grid_columnconfigure(col_idx, weight=weight, minsize=minwidth)

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
                        block_cols = value.get("layout_columns", None)
                        target_frame = ttk.LabelFrame(parent_frame, text=key, borderwidth=0, relief="flat")
                        self._create_dynamic_widgets(parent_frame=target_frame, data=value.get("fields", {}), path_prefix=current_path, override_cols=block_cols)

                    elif widget_type in self.widget_factory:
                        # Inject global context into the widget's config_data
                        value["path"] = current_path # Inject current widget's path
                        if self.state_mirror_engine:
                            value["state_mirror_engine"] = self.state_mirror_engine
                            value["base_mqtt_topic_from_path"] = self.state_mirror_engine.base_topic
                        if self.subscriber_router:
                            value["subscriber_router"] = self.subscriber_router

                        factory_kwargs = {
                            "parent_widget": parent_frame,
                            "config_data": value # Pass the modified config_data
                        }

                        try:
                            target_frame = self.widget_factory[widget_type](**factory_kwargs)
                        except Exception as e:
                            debug_logger(message=f"❌ Error creating synchronous widget '{key}' of type '{widget_type}': {e}", **_get_log_args())
                            target_frame = None
                    else:
                        debug_logger(message=f"❓ Unknown or missing widget 'type' for widget '{key}' in synchronous builder. Skipping.", **_get_log_args())

                    if target_frame:
                        tk_var = self.tk_vars.get(current_path)
                        target_frame.grid(row=row, column=col, columnspan=col_span, rowspan=row_span, padx=5, pady=5, sticky=sticky)
                        parent_frame.grid_rowconfigure(row, weight=1)
                        col += col_span
                        if col >= max_cols:
                            col = 0
                            row += row_span

        except Exception as e:
            debug_logger(message=f"❌ Error in synchronous _create_dynamic_widgets: {e}", **_get_log_args())
