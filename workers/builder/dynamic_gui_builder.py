import os
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.styling.style import DEFAULT_THEME, THEMES
from managers.configini.config_reader import Config

app_constants = Config.get_instance()

# --- 1. CORE MIXINS ---
from .core.gui_style_manager import GuiStyleMixin
from .core.gui_widget_factory import GuiWidgetFactoryMixin
from .core.gui_mqtt_manager import GuiMqttManagerMixin
from .core.gui_file_loader import GuiFileLoaderMixin
from .core.gui_rebuilder import GuiRebuilderMixin
from .core.gui_batch_builder import GuiBatchBuilderMixin

# --- 2. ADAPTERS (ISOLATED WIDGETS) ---
from .data_graphing.plot_widget_adapter import PlotWidgetAdapterMixin
from .data_graphing.meter_widget_adapter import MeterWidgetAdapterMixin

# --- 3. HIDDEN FEATURES ---
from .hidden.hidden_visibility_manager import HiddenVisibilityManagerMixin
from .hidden.hidden_geometry_manager import HiddenGeometryManagerMixin
from .hidden.hidden_breakoff_manager import HiddenBreakoffManagerMixin

# --- 4. EXISTING SIMPLE WIDGET MIXINS ---
from workers.builder.builder_input.dynamic_gui_mousewheel_mixin import MousewheelScrollMixin
from .text.dynamic_gui_create_label_from_config import LabelFromConfigCreatorMixin
from .text.dynamic_gui_create_label import LabelCreatorMixin
from .text.dynamic_gui_create_value_box import ValueBoxCreatorMixin
from workers.builder.builder_composite.dynamic_gui_create_gui_slider_value import SliderValueCreatorMixin
from workers.builder.builder_composite._Horizontal_knob_Value import HorizontalKnobValueCreatorMixin
from .input.dynamic_gui_create_gui_button_toggle import GuiButtonToggleCreatorMixin
from .input.dynamic_gui_create_gui_button_toggler import GuiButtonTogglerCreatorMixin
from .text.dynamic_gui_create_gui_dropdown_option import GuiDropdownOptionCreatorMixin
from .input.dynamic_gui_create_gui_actuator import GuiActuatorCreatorMixin
from .input.dynamic_gui_create_gui_checkbox import GuiCheckboxCreatorMixin
from .text.dynamic_gui_create_gui_listbox import GuiListboxCreatorMixin
from .images.dynamic_gui_create_progress_bar import ProgressBarCreatorMixin
from .table.dynamic_gui_table import GuiTableCreatorMixin
from .text.dynamic_gui_create_text_input import TextInputCreatorMixin
from .text.dynamic_gui_create_web_link import WebLinkCreatorMixin
from .images.dynamic_gui_create_image_display import ImageDisplayCreatorMixin
from .images.dynamic_gui_create_animation_display import AnimationDisplayCreatorMixin
from .audio.dynamic_gui_create_vu_meter import VUMeterCreatorMixin
from .input.dynamic_gui_create_fader import FaderCreatorMixin
from .input.dynamic_gui_create_inc_dec_buttons import IncDecButtonsCreatorMixin
from .input.dynamic_gui_create_directional_buttons import DirectionalButtonsCreatorMixin
from .audio.dynamic_gui_create_custom_fader import CustomFaderCreatorMixin
from .audio.dynamic_gui_create_needle_vu_meter import NeedleVUMeterCreatorMixin
from .audio.dynamic_gui_create_panner import PannerCreatorMixin
from .audio.dynamic_gui_create_trapezoid_toggler import TrapezoidButtonTogglerCreatorMixin

class DynamicGuiBuilder(
    ttk.Frame,
    # Core Logic
    GuiMqttManagerMixin,
    GuiStyleMixin,
    GuiWidgetFactoryMixin,
    GuiFileLoaderMixin,
    GuiRebuilderMixin,
    GuiBatchBuilderMixin,
    # Adapters
    PlotWidgetAdapterMixin,
    MeterWidgetAdapterMixin,
    # Hidden Features
    HiddenVisibilityManagerMixin,
    HiddenGeometryManagerMixin,
    HiddenBreakoffManagerMixin,
    # Indicators
    # Utilities & Standard Widgets
    MousewheelScrollMixin,
    LabelFromConfigCreatorMixin,
    LabelCreatorMixin,
    ValueBoxCreatorMixin,
    SliderValueCreatorMixin,
    HorizontalKnobValueCreatorMixin,
    GuiButtonToggleCreatorMixin,
    GuiButtonTogglerCreatorMixin,
    GuiDropdownOptionCreatorMixin,
    GuiActuatorCreatorMixin,
    GuiCheckboxCreatorMixin,
    GuiListboxCreatorMixin,
    ProgressBarCreatorMixin,
    GuiTableCreatorMixin,
    TextInputCreatorMixin,
    WebLinkCreatorMixin,
    ImageDisplayCreatorMixin,
    AnimationDisplayCreatorMixin,
    VUMeterCreatorMixin,
    FaderCreatorMixin,
    IncDecButtonsCreatorMixin,
    DirectionalButtonsCreatorMixin,
    CustomFaderCreatorMixin,
    NeedleVUMeterCreatorMixin,
    PannerCreatorMixin,
    TrapezoidButtonTogglerCreatorMixin
):
    def __init__(self, parent, json_path=None, tab_name=None, *args, **kwargs):
        config = kwargs.pop('config', {})
        super().__init__(master=parent)
        
        # State Initialization
        self.tab_name = tab_name
        self.state_mirror_engine = config.get('state_mirror_engine')
        self.subscriber_router = config.get('subscriber_router')
        self.json_filepath = Path(json_path) if json_path else None
        self.config_data = {}
        self.tk_vars = {}
        self.topic_widgets = {}
        self.last_build_hash = None
        self.gui_built = False

        if app_constants.global_settings['debug_enabled']:
            debug_logger(message=f"🖥️🟢 Igniting DynamicGuiBuilder for {self.tab_name}", **_get_log_args())

        # 1. Initialize Core Components
        self._initialize_mqtt_context(self.json_filepath, app_constants)
        self._initialize_widget_factory()
        self._setup_visibility_snitch() # <--- The Hidden Snitch
        self._setup_geometry_snitch()
        self._setup_breakoff_snitch()

        # 2. GUI Scaffolding
        self._apply_styles(theme_name=DEFAULT_THEME)
        self.pack(fill=tk.BOTH, expand=True)
        
        self.main_content_frame = ttk.Frame(self)
        self.main_content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        self.canvas = tk.Canvas(self.main_content_frame, background=colors["bg"], bd=0, highlightthickness=0)
        self.scroll_frame = ttk.Frame(self.canvas)
        self.scrollbar = ttk.Scrollbar(self.main_content_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scroll_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # 3. Reload Button
        if app_constants.RELOAD_CONFIG_DISPLAYED:
            self.button_frame = ttk.Frame(self)
            self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 10), padx=10)
            ttk.Button(self.button_frame, text="Reload Config", command=self._force_rebuild_gui).pack(side=tk.LEFT, pady=10)
        else:
            self.button_frame = None

        # 4. Trigger Build
        if self.json_filepath:
            self._load_and_build_from_file()
        else:
            self._rebuild_gui()
            self.gui_built = True

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event=None):
        self.canvas.itemconfig(self.canvas.find_withtag("all")[0], width=event.width, height=event.height)
