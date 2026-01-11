# builder/dynamic_gui_builder.py
#
# This file defines the main DynamicGuiBuilder class, which is responsible for constructing the application's GUI from a JSON configuration.
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
from .builder_core.gui_style_manager import GuiStyleMixin
from .builder_core.gui_widget_factory import GuiWidgetFactoryMixin
from .builder_core.gui_mqtt_manager import GuiMqttManagerMixin
from .builder_core.gui_file_loader import GuiFileLoaderMixin
from .builder_core.gui_rebuilder import GuiRebuilderMixin
from .builder_core.gui_batch_builder import GuiBatchBuilderMixin

# --- 2. ADAPTERS (ISOLATED WIDGETS) ---
from .builder_data_graphing.plot_widget_adapter import PlotWidgetAdapterMixin
from .builder_data_graphing.meter_widget_adapter import MeterWidgetAdapterMixin

# --- 3. HIDDEN FEATURES ---
from .builder_hidden.hidden_visibility_manager import HiddenVisibilityManagerMixin
from .builder_hidden.hidden_geometry_manager import HiddenGeometryManagerMixin
from .builder_hidden.hidden_breakoff_manager import HiddenBreakoffManagerMixin
from .builder_hidden.hidden_BreakLine import BreakLineCreatorMixin
from .builder_indicators.header_status_light import (
    HeaderStatusLightMixin,
)  # Add this import

# --- 4. EXISTING SIMPLE WIDGET MIXINS ---
from workers.builder.builder_input.dynamic_gui_mousewheel_mixin import (
    MousewheelScrollMixin,
)
from .builder_text.dynamic_gui_create_label_from_config import (
    LabelFromConfigCreatorMixin,
)
from .builder_text.dynamic_gui_create_label import LabelCreatorMixin
from .builder_text.dynamic_gui_create_value_box import ValueBoxCreatorMixin
from workers.builder.builder_composite.dynamic_gui_create_gui_slider_value import (
    SliderValueCreatorMixin,
)
from workers.builder.builder_composite._Horizontal_with_dial_Value import (
    HorizontalDialValueCreatorMixin,
)
from .builder_input.dynamic_gui_create_gui_button_toggle import (
    GuiButtonToggleCreatorMixin,
)
from .builder_input.dynamic_gui_create_gui_button_toggler import (
    GuiButtonTogglerCreatorMixin,
)
from .builder_text.dynamic_gui_create_gui_dropdown_option import (
    GuiDropdownOptionCreatorMixin,
)
from .builder_input.dynamic_gui_create_gui_actuator import GuiActuatorCreatorMixin
from .builder_input.dynamic_gui_create_gui_checkbox import GuiCheckboxCreatorMixin
from .builder_text.dynamic_gui_create_gui_listbox import GuiListboxCreatorMixin
from .builder_images.dynamic_gui_create_progress_bar import ProgressBarCreatorMixin
from .builder_table.dynamic_gui_table import GuiTableCreatorMixin
from .builder_text.dynamic_gui_create_text_input import TextInputCreatorMixin
from .builder_text.dynamic_gui_create_web_link import WebLinkCreatorMixin
from .builder_images.dynamic_gui_create_image_display import ImageDisplayCreatorMixin
from .builder_images.dynamic_gui_create_animation_display import (
    AnimationDisplayCreatorMixin,
)
from .builder_audio.dynamic_gui_create_vu_meter import VUMeterCreatorMixin
from .builder_input.dynamic_gui_create_fader import FaderCreatorMixin
from .builder_input.dynamic_gui_create_inc_dec_buttons import IncDecButtonsCreatorMixin
from .builder_input.dynamic_gui_create_directional_buttons import (
    DirectionalButtonsCreatorMixin,
)
from .builder_audio.dynamic_gui_create_custom_fader import CustomFaderCreatorMixin
from .builder_audio.dynamic_gui_create_needle_vu_meter import NeedleVUMeterCreatorMixin
from .builder_audio.dynamic_gui_create_panner import PannerCreatorMixin
from .builder_audio.dynamic_gui_create_trapezoid_toggler import (
    TrapezoidButtonTogglerCreatorMixin,
)
from workers.builder.builder_audio.dynamic_gui_create_knob import KnobCreatorMixin
from workers.builder.builder_audio.dynamic_gui_create_dial import DialCreatorMixin


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
    HeaderStatusLightMixin,  # Add HeaderStatusLightMixin here
    BreakLineCreatorMixin,
    # Indicators
    # Utilities & Standard Widgets
    MousewheelScrollMixin,
    LabelFromConfigCreatorMixin,
    LabelCreatorMixin,
    ValueBoxCreatorMixin,
    SliderValueCreatorMixin,
    HorizontalDialValueCreatorMixin,
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
    TrapezoidButtonTogglerCreatorMixin,
    KnobCreatorMixin,
    DialCreatorMixin,
):
    # Initializes the DynamicGuiBuilder, a comprehensive class that constructs a GUI from a JSON configuration.
    # It integrates various mixins for handling styling, widget creation, MQTT communication, and more.
    # The builder sets up the main frame, canvas for scrolling, and optionally a reload button.
    # It initializes all necessary components and triggers the GUI build process.
    # Inputs:
    #     parent (tk.Widget): The parent widget that will contain this builder frame.
    #     json_path (str, optional): The file path to the JSON configuration that defines the GUI.
    #     tab_name (str, optional): The name associated with the tab this GUI resides in.
    #     config (dict, optional): A configuration dictionary containing shared application resources
    #                              like 'state_mirror_engine' and 'subscriber_router'.
    #     *args: Additional positional arguments.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     None.
    def __init__(self, parent, json_path=None, tab_name=None, *args, **kwargs):
        """
        Initializes the DynamicGuiBuilder.

        Args:
            parent (tk.Widget): The parent widget.
            json_path (str, optional): The path to the JSON file defining the GUI. Defaults to None.
            tab_name (str, optional): The name of the tab. Defaults to None.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        
        Returns:
            None
        """
        config = kwargs.pop("config", {})
        super().__init__(master=parent)

        # State Initialization
        self.tab_name = tab_name
        self.state_mirror_engine = config.get("state_mirror_engine")
        self.subscriber_router = config.get("subscriber_router")
        if not self.state_mirror_engine:
            print(
                "CRITICAL WARNING: DynamicGuiBuilder initialized without StateMirrorEngine! Widgets will be zombies."
            )
        self.json_filepath = Path(json_path) if json_path else None
        self.config_data = {}
        self.tk_vars = {}
        self.topic_widgets = {}
        self.last_build_hash = None
        self.gui_built = False

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🖥️🟢 Igniting DynamicGuiBuilder for {self.tab_name}",
                **_get_log_args(),
            )

        # 1. Initialize Core Components
        self._initialize_mqtt_context(
            self.json_filepath,
            app_constants,
            config.get("base_mqtt_topic_from_path"),
        )
        self._initialize_widget_factory()
        self._setup_visibility_snitch()  # <--- The Hidden Snitch
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
        self.canvas = tk.Canvas(
            self.main_content_frame, background=colors["bg"], bd=0, highlightthickness=0
        )
        self.scroll_frame = ttk.Frame(self.canvas)
        self.scrollbar = ttk.Scrollbar(
            self.main_content_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )

        # Store the ID of the canvas window item for later use
        self.canvas_window_id = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scroll_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 3. Reload Button
        if app_constants.RELOAD_CONFIG_DISPLAYED:
            self.button_frame = ttk.Frame(self)
            self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 10), padx=10)
            ttk.Button(
                self.button_frame, text="Reload Config", command=self._force_rebuild_gui
            ).pack(side=tk.LEFT, pady=10)
        else:
            self.button_frame = None

        # 4. Trigger Build
        if self.json_filepath:
            self._load_and_build_from_file()
        else:
            self._rebuild_gui()
            self.gui_built = True

    # Event handler called when the scrollable frame's size or position changes.
    # This function is crucial for ensuring the scrollable area of the canvas is
    # updated to match the total size of the content within the frame.
    # Inputs:
    #     event (tk.Event, optional): The event object passed by the tkinter framework.
    # Outputs:
    #     None.
    def _on_frame_configure(self, event=None):
        """
        Event handler for when the scrollable frame is configured. It updates the scroll region of the canvas.

        Args:
            event (tk.Event, optional): The event object. Defaults to None.
        
        Returns:
            None
        """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # Event handler called when the canvas widget itself is resized.
    # This function adjusts the width of the frame window embedded within the canvas
    # to match the new width of the canvas, ensuring content flows correctly on resize.
    # Inputs:
    #     event (tk.Event, optional): The event object containing the new dimensions.
    # Outputs:
    #     None.
    def _on_canvas_configure(self, event=None):
        """
        Event handler for when the canvas is configured. It adjusts the width of the
        window item within the canvas to match the canvas's width.

        Args:
            event (tk.Event, optional): The event object. Defaults to None.

        Returns:
            None
        """
        # Update the width of the canvas window item to match the canvas width.
        # This helps prevent horizontal squashing if the canvas resizes.
        if event.width and self.canvas_window_id: # Ensure event.width is valid and window ID exists
            self.canvas.itemconfig(self.canvas_window_id, width=event.width)

        # The scrollregion update is handled by _on_frame_configure, which is bound to the
        # scroll_frame's <Configure> event. Forcing the canvas window's height to match the
        # canvas height can interfere with vertical scrolling and is generally not needed here.