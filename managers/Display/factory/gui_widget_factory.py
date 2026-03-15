# core/gui_widget_factory.py
#
# The Registry that maps JSON keys to Creator Methods.
# Optimized with lazy-loading wrappers to improve startup performance.
# Includes all helper methods to maintain "Mixin" compatibility.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260221.Factory.3

import importlib
from managers.Display.context.widget_context import WidgetContext
from managers.Display.factory.widget_registry import WidgetRegistry

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

class GuiWidgetFactoryMixin:
    """The Registry that maps JSON keys to Creator Methods using lazy loading."""

    _WIDGET_FACTORY_CACHE = None

    def _initialize_widget_factory(self):
        """Initializes the widget factory mapping."""
        if GuiWidgetFactoryMixin._WIDGET_FACTORY_CACHE is not None:
            self.widget_factory = GuiWidgetFactoryMixin._WIDGET_FACTORY_CACHE
            return

        if LOCAL_DEBUG: logger.debug("🔬 Initializing GuiWidgetFactory...")
        factory = {
            # Standard Widgets
            "_sliderValue": self.make_slider_value,
            "_Horizontal_with_dial_Value": self.make_composite_horizontal_dial_value,
            "HorizontalWithValue": self.make_composite_horizontal_dial_value,
            "_GuiButtonToggle": self.make_button_toggle,
            "_SmartToggle": self.make_button_toggle,
            "_GuiButtonToggler": self.make_button_toggler,
            "_SmartToggler": self.make_button_toggler,
            "_GuiDropDownOption": self.make_text_gui_dropdown_option,
            "_Value": self.make_text_value_box,
            "_SmartValue": self.make_text_value_box,
            "_GuiValue": self.make_text_value_box,
            "_Label": self.make_text_label_from_config,
            "_SmartLabel": self.make_text_label_from_config,
            "_GuiLabel": self.make_text_label_from_config,
            "_GuiActuator": self.make_button_actuator,
            "_SmartActuator": self.make_button_actuator,
            "_GuiButton": self.make_button_actuator,  # Added mapping
            "_GuiCheckbox": self.make_checkbox,
            "_SmartCheckbox": self.make_checkbox,
            "_GuiListbox": self.make_listbox,
            "_SmartList": self.make_listbox,
            "_ProgressBar": self.make_images_progress_bar,
            "_SmartProgress": self.make_images_progress_bar,
            "OcaTable": self.make_text_table,
            "GuiTable": self.make_text_table,
            "DynamicGuiTable": self.make_text_table,
            "DynamicGraph": self._create_plot_widget,
            "DynamicBarGraph": self._create_bar_graph_widget,
            "_SmartGraph": self._create_plot_widget,
            "_DataGraph": self._create_plot_widget,
            "_GuiGraph": self._create_plot_widget,
            "_TextInput": self.make_text_value_with_units,
            "_SmartInput": self.make_text_value_with_units,
            "_WebLink": self.make_text_web_link,
            "_SmartLink": self.make_text_web_link,
            "_ImageDisplay": self.make_images_image_display,
            "_SmartImage": self.make_images_image_display,
            "_GuiImage": self.make_images_image_display,
            "AnimationDisplay": self.make_images_animation_display,
            "_AnimationDisplay": self.make_images_animation_display,
            "_GuiAnimation": self.make_images_animation_display,
            "_SmartAnimation": self.make_images_animation_display,
            "_JsonTree": self.make_data_json_tree,
            "JsonTree": self.make_data_json_tree,
            "_BarGraph": self.make_meter_bar,
            "_SmartMeter": self.make_meter_bar,
            "_MeterBar": self.make_meter_bar,
            "MeterBar": self.make_meter_bar,
            "_Fader": self.make_fader,
            "_GuiVerticalFader": self.make_fader,  # Added mapping
            "_Knob": self.make_knob,
            "_SmartKnob": self.make_knob,
            "_GuiHorizontalKnob": self.make_knob,  # Added mapping
            "SelectorSwitch": self.make_knob_rotary_selector,
            "_SelectorSwitch": self.make_knob_rotary_selector,
            "_IncDecButtons": self.make_input_inc_dec_buttons,
            "_SmartIncDec": self.make_input_inc_dec_buttons,
            "_DirectionalButtons": self.make_input_directional_buttons,
            "_SmartNav": self.make_input_directional_buttons,
            "_CustomFader": self.make_fader,
            "_SmartFader": self.make_fader,
            "_CustomHorizontalFader": self.make_fader_horizontal,
            "_CustomDualHorizontalFader": self._lazy_wrap(
                "workers.builder.fader_dual.fader_dual",
                "BuilderFaderDualCreator",
                "make_fader_dual"
            ),
            "_CustomDualVerticalFader": self._lazy_wrap(
                "workers.builder.fader_dual.fader_dual",
                "BuilderFaderDualCreator",
                "make_fader_dual"
            ),
            "_CustomLTP": self._lazy_wrap(
                "workers.builder.fader_linear_travelling_potentiometer.fader_linear_travelling_potentiometer",
                "BuilderFaderLinearTravellingPotentiometerCreator",
                "make_fader_linear_travelling_potentiometer"
            ),
            "_NeedleVUMeter": self.make_meter_needle,
            "_GuiAnalogGauge": self.make_meter_needle,  # Added mapping
            "ProgressBar": self.make_images_progress_bar,
            "_ProgressBar": self.make_images_progress_bar,
            "_SmartProgress": self.make_images_progress_bar,
            "_TrapezoidButton": self.make_button_trapezoid,
            "_TrapezoidButtonToggler": self.make_button_trapezoid_toggler,
            "_HeaderStatusLight": self._create_status_light,
            "_SmartLight": self._create_status_light,
            "_WinkButton": self.make_button_wink,
            "_WinkButtonToggler": self.make_button_wink_toggler,
            "wink_toggler": self.make_button_wink_toggler,
            "_VUMeterKnob": self.make_meter_knob_with_vu_meter,
            "_BarGraphKnob": self.make_meter_knob_with_vu_meter,
            "_Radar": self.make_data_radar,
            "_CompositeFader": self._lazy_wrap(
                "workers.builder.fader_ganged_controlled_array.fader_ganged_controlled_array",
                "BuilderFaderGangedControlledArrayCreator",
                "make_fader_ganged_controlled_array"
            ),
            "_FaderWithBarGraph": self._lazy_wrap(
                "workers.builder.fader_bar_graph.fader_bar_graph",
                "BuilderFaderBarGraphCreator",
                "make_fader_bar_graph"
            ),
            "_MDP": self._lazy_wrap(
                "workers.builder.composite_mdp.composite_mdp",
                "BuilderCompositeMdpCreator",
                "make_composite_mdp"
            ),
            "_CMDP": self._lazy_wrap(
                "workers.builder.circular_motion_displacement_potentiometer.circular_motion_displacement_potentiometer",
                "BuilderCircularMotionDisplacementPotentiometerCreator",
                "make_circular_motion_displacement_potentiometer"
            ),
            # Complex Adapters
            "plot_widget": self._create_plot_widget,
            "_HorizontalMeterWithText": self._create_horizontal_meter,
            "_VerticalMeter": self._create_vertical_meter,
            "OcaBreakLine": self._create_break_line,
            "OcaSeparator": self._create_break_line,  # Added mapping
            "OcaFold": self._create_break_line,
            "OcaArray": self.make_array,
            "OcaCollapsibleBlock": self._create_collapsible_block,
        }

        # ⚡ MERGE REGISTRY: Overwrite/Extend with auto-discovered widgets
        # This allows new widgets to be added without modifying this file.
        registry_items = WidgetRegistry._registry
        if registry_items:
            if LOCAL_DEBUG: logger.debug(f"🧩 Merging {len(registry_items)} widgets from Registry into Factory.")
            for widget_type, creator_class in registry_items.items():
                # Create a closure to capture the class
                def make_wrapper(cls_ref):
                    def wrapper(parent_widget, config_data, context=None, **kwargs):
                        # Ensure we have a context or at least the builder instance
                        # In the transition phase, 'self' here is the Builder instance.
                        if hasattr(cls_ref, 'make'):
                            # New Style: Static make()
                            # Pass 'self' as builder_instance in kwargs if context is missing app_instance
                            if context and not hasattr(context, 'app_instance'):
                                kwargs['builder_instance'] = self
                            elif not context:
                                kwargs['builder_instance'] = self
                            return cls_ref.make(parent_widget, config_data, context, **kwargs)
                        else:
                            # Fallback? Should not happen if correctly decorated
                            logger.warning(f"⚠️ Registry class {cls_ref} missing static 'make' method.")
                            return None
                    return wrapper
                
                factory[widget_type] = make_wrapper(creator_class)

        GuiWidgetFactoryMixin._WIDGET_FACTORY_CACHE = factory
        self.widget_factory = factory

    # --- Generic Lazy Wrapper Generator ---
    def _lazy_wrap(self, module_path, class_name, method_name):
        def wrapper(parent_widget, config_data, context: WidgetContext = None, **kwargs):
            module = importlib.import_module(module_path)
            creator_class = getattr(module, class_name)
            method = getattr(creator_class, method_name)
            return method(self, parent_widget, config_data, context=context, **kwargs)
        return wrapper

    # --- Lazy Loading Methods (Creators & Helpers) ---

    # 1. Knob Creator & Helpers
    def make_knob(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.knob.knob import BuilderKnobCreator
        return BuilderKnobCreator.make_knob(self, parent_widget, config_data, context=context, **kwargs)
    def _draw_knob(self, *args, **kwargs):
        from workers.builder.knob.core.knob_renderer import draw_knob_visuals
        return draw_knob_visuals(*args, **kwargs)
    def _draw_body(self, *args, **kwargs):
        from workers.builder.knob.core.knob_renderer import _draw_body
        return _draw_body(*args, **kwargs)
    def _draw_track(self, *args, **kwargs):
        from workers.builder.knob.core.knob_renderer import _draw_track
        return _draw_track(*args, **kwargs)
    def _draw_ticks(self, *args, **kwargs):
        from workers.builder.knob.core.knob_renderer import _draw_ticks
        return _draw_ticks(*args, **kwargs)
    def _draw_pointer(self, *args, **kwargs):
        from workers.builder.knob.core.knob_renderer import _draw_pointer
        return _draw_pointer(*args, **kwargs)
    def _get_poly_points(self, *args, **kwargs):
        from workers.builder.knob.core.knob_renderer import _get_poly_points
        return _get_poly_points(*args, **kwargs)
    def _draw_gear_points(self, *args, **kwargs):
        from workers.builder.knob.core.knob_renderer import _get_gear_points
        return _get_gear_points(*args, **kwargs)

    # 2. Fader Creator & Helpers
    def make_fader(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.fader.fader import BuilderFaderCreator
        return BuilderFaderCreator.make_fader(self, parent_widget, config_data, context=context, **kwargs)
    def _draw_fader(self, *args, **kwargs):
        from workers.builder.fader.fader import BuilderFaderCreator
        return BuilderFaderCreator._draw_fader(self, *args, **kwargs)
    def _draw_rounded_rectangle(self, *args, **kwargs):
        from workers.builder.fader.fader import BuilderFaderCreator
        return BuilderFaderCreator._draw_rounded_rectangle(self, *args, **kwargs)
    def _sync_fader_cap_position(self, *args, **kwargs):
        from workers.builder.fader.fader import BuilderFaderCreator
        return BuilderFaderCreator._sync_fader_cap_position(self, *args, **kwargs)

    # 3. Horizontal Fader Creator & Helpers
    def make_fader_horizontal(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.fader_horizontal.fader_horizontal import BuilderFaderHorizontalCreator
        return BuilderFaderHorizontalCreator.make_fader_horizontal(self, parent_widget, config_data, context=context, **kwargs)
    def _draw_horizontal_fader(self, *args, **kwargs):
        from workers.builder.fader_horizontal.fader_horizontal import BuilderFaderHorizontalCreator
        return BuilderFaderHorizontalCreator._draw_horizontal_fader(self, *args, **kwargs)

    # 4. LTP Creator & Helpers
    def make_fader_linear_travelling_potentiometer(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.fader_linear_travelling_potentiometer.fader_linear_travelling_potentiometer import BuilderFaderLinearTravellingPotentiometerCreator
        return BuilderFaderLinearTravellingPotentiometerCreator.make_fader_linear_travelling_potentiometer(self, parent_widget, config_data, context=context, **kwargs)
    def _draw_ltp_knob(self, *args, **kwargs):
        from workers.builder.fader_linear_travelling_potentiometer.fader_linear_travelling_potentiometer import BuilderFaderLinearTravellingPotentiometerCreator
        return BuilderFaderLinearTravellingPotentiometerCreator._draw_ltp_knob(self, *args, **kwargs)
    def _draw_ltp_horizontal(self, *args, **kwargs):
        from workers.builder.fader_linear_travelling_potentiometer.fader_linear_travelling_potentiometer import BuilderFaderLinearTravellingPotentiometerCreator
        return BuilderFaderLinearTravellingPotentiometerCreator._draw_ltp_horizontal(self, *args, **kwargs)
    def _draw_ltp_vertical(self, *args, **kwargs):
        from workers.builder.fader_linear_travelling_potentiometer.fader_linear_travelling_potentiometer import BuilderFaderLinearTravellingPotentiometerCreator
        return BuilderFaderLinearTravellingPotentiometerCreator._draw_ltp_vertical(self, *args, **kwargs)

    # 5. Meter Needle Creator & Helpers
    def make_meter_needle(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.meter_needle.meter_needle import BuilderMeterNeedleCreator
        return BuilderMeterNeedleCreator.make_meter_needle(self, parent_widget, config_data, context=context, **kwargs)
    def _draw_needle_vu_meter(self, *args, **kwargs):
        from workers.builder.meter_needle.meter_needle import BuilderMeterNeedleCreator
        return BuilderMeterNeedleCreator._draw_needle_vu_meter(self, *args, **kwargs)

    # 6. Actuator Creator & Helpers
    def make_button_actuator(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.button_actuator.button_actuator import BuilderButtonActuatorCreator
        return BuilderButtonActuatorCreator.make_button_actuator(self, parent_widget, config_data, context=context, **kwargs)
    def _on_actuator_state_update(self, *args, **kwargs):
        from workers.builder.button_actuator.button_actuator import BuilderButtonActuatorCreator
        return BuilderButtonActuatorCreator._on_actuator_state_update(self, *args, **kwargs)

    # 7. Composite Fader Dial Creator & Helpers
    def make_composite_horizontal_dial_value(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.composite_horizontal_dial_value.composite_horizontal_dial_value import BuilderCompositeHorizontalDialValueCreator
        return BuilderCompositeHorizontalDialValueCreator.make_composite_horizontal_dial_value(self, parent_widget, config_data, context=context, **kwargs)
    def _get_format_string(self, *args, **kwargs):
        from workers.builder.composite_horizontal_dial_value.composite_horizontal_dial_value import BuilderCompositeHorizontalDialValueCreator
        return BuilderCompositeHorizontalDialValueCreator._get_format_string(self, *args, **kwargs)

    # 8. Array Creator & Helpers
    def make_array(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from managers.Display.array.array import BuilderArrayCreator
        return BuilderArrayCreator.make_array(self, parent_widget, config_data, context=context, **kwargs)
    def _inject_data(self, *args, **kwargs):
        from managers.Display.array.array import BuilderArrayCreator
        return BuilderArrayCreator._inject_data(self, *args, **kwargs)
    def _inject_view_manager(self, *args, **kwargs):
        from managers.Display.array.array import BuilderArrayCreator
        return BuilderArrayCreator._inject_view_manager(self, *args, **kwargs)
    def _resolve_placeholder(self, *args, **kwargs):
        from managers.Display.array.array import BuilderArrayCreator
        return BuilderArrayCreator._resolve_placeholder(self, *args, **kwargs)

    # 9. Trapezoid Button Creator & Helpers
    def make_button_trapezoid(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.button_trapezoid.button_trapezoid import BuilderButtonTrapezoidCreator
        return BuilderButtonTrapezoidCreator.make_button_trapezoid(self, parent_widget, config_data, context=context, **kwargs)
    def _draw_trapezoid_button(self, *args, **kwargs):
        from workers.builder.button_trapezoid.button_trapezoid import BuilderButtonTrapezoidCreator
        return BuilderButtonTrapezoidCreator._draw_trapezoid_button(self, *args, **kwargs)
    def _adjust_color(self, *args, **kwargs):
        from workers.builder.button_trapezoid.button_trapezoid import BuilderButtonTrapezoidCreator
        return BuilderButtonTrapezoidCreator._adjust_color(self, *args, **kwargs)

    # 10. Label Creator & Helpers
    def make_text_label(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.text_label.text_label import BuilderTextLabelCreator
        return BuilderTextLabelCreator.make_text_label(self, parent_widget, config_data, context=context, **kwargs)

    def make_text_label_from_config(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.text_label_from_config.text_label_from_config import BuilderTextLabelFromConfigCreator
        return BuilderTextLabelFromConfigCreator.make_text_label_from_config(self, parent_widget, config_data, context=context, **kwargs)

    # 11. Listbox Creator & Helpers
    def make_listbox(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.listbox.listbox import BuilderListboxCreator
        return BuilderListboxCreator.make_listbox(self, parent_widget, config_data, context=context, **kwargs)
    def _rebuild_listbox_display_instance(self, *args, **kwargs):
        from workers.builder.listbox.listbox import BuilderListboxCreator
        return BuilderListboxCreator._rebuild_listbox_display_instance(self, *args, **kwargs)
    def _on_option_mqtt_update_instance(self, *args, **kwargs):
        from workers.builder.listbox.listbox import BuilderListboxCreator
        return BuilderListboxCreator._on_option_mqtt_update_instance(self, *args, **kwargs)

    # 12. Simple Wrappers
    def make_slider_value(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.slider_value.slider_value import BuilderSliderValueCreator
        return BuilderSliderValueCreator.make_slider_value(self, parent_widget, config_data, context=context, **kwargs)
    def make_button_toggle(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.button_toggle.button_toggle import BuilderButtonToggleCreator
        return BuilderButtonToggleCreator.make_button_toggle(self, parent_widget, config_data, context=context, **kwargs)
    def make_button_toggler(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.button_toggler.button_toggler import BuilderButtonTogglerCreator
        return BuilderButtonTogglerCreator.make_button_toggler(self, parent_widget, config_data, context=context, **kwargs)
    def make_text_gui_dropdown_option(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.text_gui_dropdown_option.text_gui_dropdown_option import BuilderTextGuiDropdownOptionCreator
        return BuilderTextGuiDropdownOptionCreator.make_text_gui_dropdown_option(self, parent_widget, config_data, context=context, **kwargs)
    def make_text_value_box(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.text_value_box.text_value_box import BuilderTextValueBoxCreator
        return BuilderTextValueBoxCreator.make_text_value_box(self, parent_widget, config_data, context=context, **kwargs)
    def make_checkbox(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.checkbox.checkbox import BuilderCheckboxCreator
        return BuilderCheckboxCreator.make_checkbox(self, parent_widget, config_data, context=context, **kwargs)
    def make_images_progress_bar(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.images_progress_bar.images_progress_bar import BuilderImagesProgressBarCreator
        return BuilderImagesProgressBarCreator.make_images_progress_bar(self, parent_widget, config_data, context=context, **kwargs)
    def make_text_table(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.text_table.text_table import BuilderTextTableCreator
        return BuilderTextTableCreator.make_text_table(self, parent_widget, config_data, context=context, **kwargs)
    def _create_plot_widget(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.data_graphing.plot_widget_adapter import PlotWidgetAdapterMixin
        return PlotWidgetAdapterMixin._create_plot_widget(self, parent_widget, config_data, context=context, **kwargs)
    def _create_bar_graph_widget(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.data_graphing.plot_widget_adapter import PlotWidgetAdapterMixin
        return PlotWidgetAdapterMixin._create_bar_graph_widget(self, parent_widget, config_data, context=context, **kwargs)
    def make_text_value_with_units(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.text_value_with_units.text_value_with_units import BuilderTextValueWithUnitsCreator
        return BuilderTextValueWithUnitsCreator.make_text_value_with_units(self, parent_widget, config_data, context=context, **kwargs)
    def make_text_web_link(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.text_web_link.text_web_link import BuilderTextWebLinkCreator
        return BuilderTextWebLinkCreator.make_text_web_link(self, parent_widget, config_data, context=context, **kwargs)
    def make_images_image_display(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.images_image_display.images_image_display import BuilderImagesImageDisplayCreator
        return BuilderImagesImageDisplayCreator.make_images_image_display(self, parent_widget, config_data, context=context, **kwargs)
    def make_images_animation_display(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.images_animation_display.images_animation_display import BuilderImagesAnimationDisplayCreator
        return BuilderImagesAnimationDisplayCreator.make_images_animation_display(self, parent_widget, config_data, context=context, **kwargs)
    def make_data_json_tree(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.data_json_tree.data_json_tree import BuilderDataJsonTreeCreator
        return BuilderDataJsonTreeCreator.make_data_json_tree(self, parent_widget, config_data, context=context, **kwargs)
    def _refresh_tree(self, *args, **kwargs):
        from workers.builder.data_json_tree.data_json_tree import BuilderDataJsonTreeCreator
        return BuilderDataJsonTreeCreator._refresh_tree(self, *args, **kwargs)
    def make_meter_bar(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.meter_bar.meter_bar import BuilderMeterBarCreator
        return BuilderMeterBarCreator.make_meter_bar(parent_widget, config_data, context=context, **kwargs)
    def make_knob_rotary_selector(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.knob_rotary_selector.knob_rotary_selector import BuilderKnobRotarySelectorCreator
        return BuilderKnobRotarySelectorCreator.make_knob_rotary_selector(self, parent_widget, config_data, context=context, **kwargs)
    def make_input_inc_dec_buttons(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.input_inc_dec_buttons.input_inc_dec_buttons import BuilderInputIncDecButtonsCreator
        return BuilderInputIncDecButtonsCreator.make_input_inc_dec_buttons(self, parent_widget, config_data, context=context, **kwargs)
    def make_input_directional_buttons(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.input_directional_buttons.input_directional_buttons import BuilderInputDirectionalButtonsCreator
        return BuilderInputDirectionalButtonsCreator.make_input_directional_buttons(self, parent_widget, config_data, context=context, **kwargs)
    def make_fader_horizontal_dual(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.fader_horizontal_dual.fader_horizontal_dual import BuilderFaderHorizontalDualCreator
        return BuilderFaderHorizontalDualCreator.make_fader_horizontal_dual(self, parent_widget, config_data, context=context, **kwargs)
    def make_button_trapezoid_toggler(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.button_trapezoid_toggler.button_trapezoid_toggler import BuilderButtonTrapezoidTogglerCreator
        return BuilderButtonTrapezoidTogglerCreator.make_button_trapezoid_toggler(self, parent_widget, config_data, context=context, **kwargs)
    def make_button_wink(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.button_wink.button_wink import BuilderButtonWinkCreator
        return BuilderButtonWinkCreator.make_button_wink(self, parent_widget, config_data, context=context, **kwargs)
    def make_button_wink_toggler(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.button_wink_toggler.button_wink_toggler import BuilderButtonWinkTogglerCreator
        return BuilderButtonWinkTogglerCreator.make_button_wink_toggler(self, parent_widget, config_data, context=context, **kwargs)
    def make_meter_knob_with_vu_meter(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.meter_knob_with_vu_meter.meter_knob_with_vu_meter import BuilderMeterKnobWithVuMeterCreator
        return BuilderMeterKnobWithVuMeterCreator.make_meter_knob_with_vu_meter(self, parent_widget, config_data, context=context, **kwargs)
    def make_data_radar(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.data_radar.data_radar import BuilderDataRadarCreator
        return BuilderDataRadarCreator.make_data_radar(self, parent_widget, config_data, context=context, **kwargs)
    def make_fader_ganged_controlled_array(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.fader_ganged_controlled_array.fader_ganged_controlled_array import BuilderFaderGangedControlledArrayCreator
        return BuilderFaderGangedControlledArrayCreator.make_fader_ganged_controlled_array(self, parent_widget, config_data, context=context, **kwargs)
    def make_fader_bar_graph(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.fader_bar_graph.fader_bar_graph import BuilderFaderBarGraphCreator
        return BuilderFaderBarGraphCreator.make_fader_bar_graph(self, parent_widget, config_data, context=context, **kwargs)
    def make_composite_mdp(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.composite_mdp.composite_mdp import BuilderCompositeMdpCreator
        return BuilderCompositeMdpCreator.make_composite_mdp(self, parent_widget, config_data, context=context, **kwargs)
    def make_circular_motion_displacement_potentiometer(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.circular_motion_displacement_potentiometer.circular_motion_displacement_potentiometer import BuilderCircularMotionDisplacementPotentiometerCreator
        return BuilderCircularMotionDisplacementPotentiometerCreator.make_circular_motion_displacement_potentiometer(self, parent_widget, config_data, context=context, **kwargs)
    def _create_horizontal_meter(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.data_graphing.meter_widget_adapter import MeterWidgetAdapterMixin
        return MeterWidgetAdapterMixin._create_horizontal_meter(self, parent_widget, config_data, context=context, **kwargs)
    def _create_vertical_meter(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.data_graphing.meter_widget_adapter import MeterWidgetAdapterMixin
        return MeterWidgetAdapterMixin._create_vertical_meter(self, parent_widget, config_data, context=context, **kwargs)
    def _create_break_line(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.break_line.hidden_BreakLine import BreakLineCreatorMixin
        return BreakLineCreatorMixin._create_break_line(self, parent_widget, config_data, context=context, **kwargs)
    def _create_collapsible_block(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from managers.Display.array.collapsible_block.collapsible_block import CollapsibleBlockCreatorMixin
        return CollapsibleBlockCreatorMixin._create_collapsible_block(self, parent_widget, config_data, context=context, **kwargs)

    def _create_status_light(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        from workers.builder.status_light.status_light import HeaderStatusLightMixin
        return HeaderStatusLightMixin._build_header_status_light(self, parent_widget, config_data, context=context, **kwargs)

    def _build_header_status_light(self, *args, **kwargs):
        from workers.builder.status_light.status_light import HeaderStatusLightMixin
        return HeaderStatusLightMixin._build_header_status_light(self, parent_widget, config_data, context=context, **kwargs)
    def _update_status_light(self, *args, **kwargs):
        from workers.builder.status_light.status_light import HeaderStatusLightMixin
        return HeaderStatusLightMixin._update_status_light(self, *args, **kwargs)
