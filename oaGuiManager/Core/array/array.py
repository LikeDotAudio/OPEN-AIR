# Core/array/array.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2355.1
#
# Description: Generates a data-driven grid of widgets by expanding a blueprint.

import tkinter as tk
import inspect
import orjson
from typing import Dict, Any, List, Optional
from loguru import logger

from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config
from oaGuiManager.Core.context.widget_context import WidgetContext
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

app_constants = Config.get_instance()

class ViewManager:
    """Manages visibility groups and right-click toggle menus for collapsible sections."""
    def __init__(self, root_widget: tk.Widget):
        self.groups = {}
        self.vars = {}
        self.menu = tk.Menu(root_widget, tearoff=0)

    def register(self, group_name: str, widget: tk.Widget):
        """Registers a widget into a visibility group."""
        if group_name not in self.groups:
            self._initialize_group(group_name)
        self.groups[group_name].append(widget)

    def _initialize_group(self, group_name: str):
        self.groups[group_name] = []
        var = tk.BooleanVar(value=True)
        self.vars[group_name] = var
        self.menu.add_checkbutton(
            label=f"Show {group_name}",
            variable=var,
            command=lambda g=group_name: self._toggle_group(g)
        )

    def _toggle_group(self, group_name: str):
        is_visible = self.vars[group_name].get()
        state = "expanded" if is_visible else "collapsed"
        for widget in self.groups.get(group_name, []):
            if hasattr(widget, "set_view_state"):
                widget.set_view_state(state)

    def show_menu(self, event):
        """Displays the visibility toggle menu."""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

class GridColumnConfigurator:
    """Encapsulates Tkinter grid column management logic."""
    @staticmethod
    def apply_sizing(container: tk.Widget, num_columns: int, sizing_info: List[Dict]):
        """Configures grid weights and minimum sizes for the target container."""
        for col_idx in range(num_columns):
            info = sizing_info[col_idx] if col_idx < len(sizing_info) else {}
            weight = info.get("weight", 1)
            minwidth = info.get("minwidth", 0)
            maxwidth = info.get("maxwidth", 0)

            # ⚡ CONSTRAINT: Enforce fixed width if maxwidth is specified
            if maxwidth > 0:
                minwidth = maxwidth
                weight = 0

            container.grid_columnconfigure(col_idx, weight=weight, minsize=minwidth)

class BlueprintDataInjector:
    """Handles recursive injection of data and view managers into JSON blueprints."""
    @classmethod
    def inject(cls, config: Any, data: Dict, view_manager: Optional[ViewManager] = None):
        """Recursively injects data context and view manager into the configuration."""
        if isinstance(config, dict):
            cls._inject_into_dict(config, data, view_manager)
        elif isinstance(config, list):
            cls._inject_into_list(config, data, view_manager)

    @classmethod
    def _inject_into_dict(cls, config: Dict, data: Dict, vm: Optional[ViewManager]):
        # Specific injection for collapsible blocks
        if config.get("type") == "OcaCollapsibleBlock" and vm:
            config["_view_manager"] = vm

        for key, value in config.items():
            if isinstance(value, (dict, list)):
                cls.inject(value, data, vm)
            elif isinstance(value, str) and "{{" in value:
                config[key] = cls._resolve_string_placeholders(value, data)

    @classmethod
    def _inject_into_list(cls, config: List, data: Dict, vm: Optional[ViewManager]):
        for i, value in enumerate(config):
            if isinstance(value, (dict, list)):
                cls.inject(value, data, vm)
            elif isinstance(value, str) and "{{" in value:
                config[i] = cls._resolve_string_placeholders(value, data)

    @staticmethod
    def _resolve_string_placeholders(text: str, data: Dict) -> Any:
        """Replaces {{key}} placeholders with values from the data context."""
        for key, val in data.items():
            placeholder = f"{{{{{key}}}}}"
            if text == placeholder:
                return val
            if placeholder in text:
                text = text.replace(placeholder, str(val))
        return text

class ArrayDataExpander:
    """Orchestrates the expansion of a blueprint into a data-mapped item set."""
    @staticmethod
    def expand_blueprint(blueprint: Dict, data_array: List[Dict], view_manager: ViewManager) -> Dict[str, Any]:
        """Creates a collection of item configurations by mapping data to a blueprint."""
        synthetic_fields = {}
        # Use orjson for optimized string template generation
        blueprint_template = orjson.dumps(blueprint).decode()

        for idx, item in enumerate(data_array):
            item_id = str(item.get("id", f"item_{idx}"))
            try:
                # Materialize item configuration from template
                item_config = orjson.loads(blueprint_template)
                BlueprintDataInjector.inject(item_config, item, view_manager)
                synthetic_fields[item_id] = item_config
            except Exception as e:
                logger.error(f"ArrayExpander: Failed to materialize element {idx}: {e}")
        
        return synthetic_fields

class BuilderArrayCreator(TransparencyMixin):
    """
    Main orchestrator for data-driven Array widgets.
    Coordinates container setup, data expansion, and batch rendering handoff.
    """
    
    @staticmethod
    def make(parent_widget, config_data, context: WidgetContext = None, **kwargs):
        """Factory entry point."""
        return BuilderArrayCreator().create(parent_widget, config_data, context, **kwargs)

    def create(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        """Orchestrates the full lifecycle of array widget creation."""
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, 
                   f"🧱 ArrayCreator: Initializing data-driven array at {config_data.get('path')}", level="DEBUG")

        # 1. Scaffolding
        main_container = self._setup_scaffolding(parent_widget, config_data, context, **kwargs)
        view_manager = ViewManager(main_container)
        main_container.bind("<Button-3>", view_manager.show_menu)

        # 2. Grid Management
        grid_container = self._setup_grid_container(main_container, config_data, context, view_manager, **kwargs)
        
        # 3. Data-Driven Expansion
        synthetic_fields = self._expand_data_to_fields(config_data, view_manager)
        
        # 4. Asynchronous Build Handoff
        self._dispatch_batch_build(grid_container, config_data, synthetic_fields, context, **kwargs)

        return main_container

    def _setup_scaffolding(self, parent, config, context, **kwargs) -> tk.Canvas:
        """Creates and configures the outer shell container."""
        p_bg = "#2b2b2b"
        try: p_bg = parent.cget("bg")
        except: pass

        container = tk.Canvas(parent, bd=0, highlightthickness=0, relief="flat", bg=p_bg)
        
        # Enforce geometry constraints if provided
        geom = config.get("geometry", {})
        width = config.get("width") or geom.get("width")
        height = config.get("height") or geom.get("height")
        
        if width or height:
            container.grid_propagate(False)
            container.pack_propagate(False)
            if width: container.config(width=width)
            if height: container.config(height=height)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        builder = getattr(context, 'builder_instance', kwargs.get('builder_instance', self))
        self._apply_transparency(container, container, config, builder)
        return container

    def _setup_grid_container(self, parent, config, context, view_manager, **kwargs) -> tk.Canvas:
        """Creates the inner grid container and configures its columns."""
        grid_container = tk.Canvas(parent, bd=0, highlightthickness=0, relief="flat")
        grid_container.grid(row=0, column=0, sticky="nsew")
        grid_container.bind("<Button-3>", view_manager.show_menu)
        
        builder = getattr(context, 'builder_instance', kwargs.get('builder_instance'))
        self._apply_transparency(grid_container, grid_container, config, builder)

        # Separate column logic from array expansion
        layout_cols = config.get("layout_columns", 8)
        GridColumnConfigurator.apply_sizing(grid_container, layout_cols, config.get("column_sizing", []))
        
        return grid_container

    def _expand_data_to_fields(self, config: Dict, view_manager: ViewManager) -> Dict:
        """Transforms data array into a set of item configurations using the blueprint."""
        data_array = config.get("data", [])
        blueprint = config.get("blueprint", {})
        blocks = config.get("blocks") or config.get("fields")

        if data_array:
            return ArrayDataExpander.expand_blueprint(blueprint, data_array, view_manager)
        
        # Fallback to static blocks if no data array is provided
        return blocks or {}

    def _dispatch_batch_build(self, container, config, fields, context, **kwargs):
        """Hands off the expanded item set to the BatchBuilder engine."""
        if not fields:
            on_complete = getattr(context, 'on_complete', kwargs.get('on_complete'))
            if on_complete: on_complete()
            return

        batch_config = {
            "type": "OcaBlock", 
            "layout_columns": config.get("layout_columns", 8),
            "column_sizing": config.get("column_sizing", []),
            "fields": fields,
            "show_label": False,
            "layout": config.get("layout", {}) 
        }

        builder = getattr(context, 'builder_instance', kwargs.get('builder_instance'))
        if builder:
            builder._create_dynamic_widgets(
                container, batch_config, 
                path_prefix=config.get("path", ""), 
                on_complete=getattr(context, 'on_complete', kwargs.get('on_complete')),
                context=context
            )
