class GuiWidgetFactoryMixin:
    """The Registry that maps JSON keys to Creator Methods."""

    def _initialize_widget_factory(self):
        self.widget_factory = {
            # Standard Widgets
            "_sliderValue": self._create_slider_value,
            "_Horizontal_knob_Value": self._create_horizontal_knob_value,
            "_GuiButtonToggle": self._create_gui_button_toggle,
            "_GuiButtonToggler": self._create_gui_button_toggler,
            "_GuiDropDownOption": self._create_gui_dropdown_option,
            "_Value": self._create_value_box,
            "_Label": self._create_label_from_config,
            "_GuiActuator": self._create_gui_actuator,
            "_GuiCheckbox": self._create_gui_checkbox,
            "_GuiListbox": self._create_gui_listbox,
            "_ProgressBar": self._create_progress_bar,
            "OcaTable": self._create_gui_table,
            "_TextInput": self._create_text_input,
            "_WebLink": self._create_web_link,
            "_ImageDisplay": self._create_image_display,
            "_AnimationDisplay": self._create_animation_display,
            "_VUMeter": self._create_vu_meter,
            "_Fader": self._create_fader,
            "_Knob": self._create_knob,
            "_IncDecButtons": self._create_inc_dec_buttons,
            "_DirectionalButtons": self._create_directional_buttons,
            "_CustomFader": self._create_custom_fader,
            "_CustomHorizontalFader": self._create_custom_horizontal_fader,
            "_NeedleVUMeter": self._create_needle_vu_meter,
            "_Panner": self._create_panner,
            "_TrapezoidButton": self._create_trapezoid_button,
            "_TrapezoidButtonToggler": self._create_trapezoid_button_toggler,
            "_HeaderStatusLight": self._create_header_status_light,
            
            # Complex Adapters (Methods inherited from Adapter Mixins)
            "plot_widget": self._create_plot_widget,
            "_HorizontalMeterWithText": self._create_horizontal_meter,
            "_VerticalMeter": self._create_vertical_meter
        }

    def _create_header_status_light(self, parent_widget, config_data):
        # label = config_data.get("label_active", "") # Label is not directly used here
        self._build_header_status_light(parent_widget, config_data)
        return self.header_frame # Assuming _build_header_status_light creates and sets self.header_frame

