# core/gui_widget_factory.py
# Modularized GUI Widget Factory.
# Version 20260315.Modular.1

import importlib
from loguru import logger
from managers.Display.context.widget_context import WidgetContext
from managers.Display.factory.core.factory_mapping import get_core_factory_mapping
from managers.Display.factory.core.widget_discovery_engine import WidgetDiscoveryEngine

class GuiWidgetFactoryMixin:
    """The Registry that maps JSON keys to Creator Methods using lazy loading."""

    _WIDGET_FACTORY_CACHE = None

    def _initialize_widget_factory(self):
        if GuiWidgetFactoryMixin._WIDGET_FACTORY_CACHE is not None:
            self.widget_factory = GuiWidgetFactoryMixin._WIDGET_FACTORY_CACHE; return

        logger.debug("🔬 Initializing GuiWidgetFactory...")
        factory = get_core_factory_mapping(self)
        factory = WidgetDiscoveryEngine.merge_registry(factory, self)

        GuiWidgetFactoryMixin._WIDGET_FACTORY_CACHE = factory
        self.widget_factory = factory

    def _lazy_wrap(self, module_path, class_name, method_name):
        def wrapper(parent_widget, config_data, context: WidgetContext = None, **kwargs):
            module = importlib.import_module(module_path)
            method = getattr(getattr(module, class_name), method_name)
            return method(self, parent_widget, config_data, context=context, **kwargs)
        return wrapper

    # --- Widget Adapters (Bridge to Specific Creators) ---
    
    def make_knob(self, *args, **kwargs):
        from workers.builder.knob.knob import BuilderKnobCreator
        return BuilderKnobCreator.make_knob(self, *args, **kwargs)

    def make_fader(self, *args, **kwargs):
        from workers.builder.fader.fader import BuilderFaderCreator
        return BuilderFaderCreator.make_fader(self, *args, **kwargs)

    def make_fader_horizontal(self, *args, **kwargs):
        from workers.builder.fader_horizontal.fader_horizontal import BuilderFaderHorizontalCreator
        return BuilderFaderHorizontalCreator.make_fader_horizontal(self, *args, **kwargs)

    def make_fader_linear_travelling_potentiometer(self, *args, **kwargs):
        from workers.builder.fader_linear_travelling_potentiometer.fader_linear_travelling_potentiometer import BuilderFaderLinearTravellingPotentiometerCreator
        return BuilderFaderLinearTravellingPotentiometerCreator.make_fader_linear_travelling_potentiometer(self, *args, **kwargs)

    def make_meter_needle(self, *args, **kwargs):
        from workers.builder.meter_needle.meter_needle import BuilderMeterNeedleCreator
        return BuilderMeterNeedleCreator.make_meter_needle(self, *args, **kwargs)

    def make_button_actuator(self, *args, **kwargs):
        from workers.builder.button_actuator.button_actuator import BuilderButtonActuatorCreator
        return BuilderButtonActuatorCreator.make_button_actuator(self, *args, **kwargs)

    def make_composite_horizontal_dial_value(self, *args, **kwargs):
        from workers.builder.composite_horizontal_dial_value.composite_horizontal_dial_value import BuilderCompositeHorizontalDialValueCreator
        return BuilderCompositeHorizontalDialValueCreator.make_composite_horizontal_dial_value(self, *args, **kwargs)

    def make_array(self, *args, **kwargs):
        from managers.Display.array.array import BuilderArrayCreator
        return BuilderArrayCreator.make_array(self, *args, **kwargs)

    def make_button_trapezoid(self, *args, **kwargs):
        from workers.builder.button_trapezoid.button_trapezoid import BuilderButtonTrapezoidCreator
        return BuilderButtonTrapezoidCreator.make_button_trapezoid(self, *args, **kwargs)

    def make_text_label(self, *args, **kwargs):
        from workers.builder.text_label.text_label import BuilderTextLabelCreator
        return BuilderTextLabelCreator.make_text_label(self, *args, **kwargs)

    def make_text_label_from_config(self, *args, **kwargs):
        from workers.builder.text_label_from_config.text_label_from_config import BuilderTextLabelFromConfigCreator
        return BuilderTextLabelFromConfigCreator.make_text_label_from_config(self, *args, **kwargs)

    def make_listbox(self, *args, **kwargs):
        from workers.builder.listbox.listbox import BuilderListboxCreator
        return BuilderListboxCreator.make_listbox(self, *args, **kwargs)

    def make_slider_value(self, *args, **kwargs):
        from workers.builder.slider_value.slider_value import BuilderSliderValueCreator
        return BuilderSliderValueCreator.make_slider_value(self, *args, **kwargs)

    def make_button_toggle(self, *args, **kwargs):
        from workers.builder.button_toggle.button_toggle import BuilderButtonToggleCreator
        return BuilderButtonToggleCreator.make_button_toggle(self, *args, **kwargs)

    def make_button_toggler(self, *args, **kwargs):
        from workers.builder.button_toggler.button_toggler import BuilderButtonTogglerCreator
        return BuilderButtonTogglerCreator.make_button_toggler(self, *args, **kwargs)

    def make_text_gui_dropdown_option(self, *args, **kwargs):
        from workers.builder.text_gui_dropdown_option.text_gui_dropdown_option import BuilderTextGuiDropdownOptionCreator
        return BuilderTextGuiDropdownOptionCreator.make_text_gui_dropdown_option(self, *args, **kwargs)

    def make_text_value_box(self, *args, **kwargs):
        from workers.builder.text_value_box.text_value_box import BuilderTextValueBoxCreator
        return BuilderTextValueBoxCreator.make_text_value_box(self, *args, **kwargs)

    def make_checkbox(self, *args, **kwargs):
        from workers.builder.checkbox.checkbox import BuilderCheckboxCreator
        return BuilderCheckboxCreator.make_checkbox(self, *args, **kwargs)

    def make_images_progress_bar(self, *args, **kwargs):
        from workers.builder.images_progress_bar.images_progress_bar import BuilderImagesProgressBarCreator
        return BuilderImagesProgressBarCreator.make_images_progress_bar(self, *args, **kwargs)

    def make_text_table(self, *args, **kwargs):
        from workers.builder.text_table.text_table import BuilderTextTableCreator
        return BuilderTextTableCreator.make_text_table(self, *args, **kwargs)

    def _create_plot_widget(self, *args, **kwargs):
        from workers.builder.data_graphing.plot_widget_adapter import PlotWidgetAdapterMixin
        return PlotWidgetAdapterMixin._create_plot_widget(self, *args, **kwargs)

    def _create_bar_graph_widget(self, *args, **kwargs):
        from workers.builder.data_graphing.plot_widget_adapter import PlotWidgetAdapterMixin
        return PlotWidgetAdapterMixin._create_bar_graph_widget(self, *args, **kwargs)

    def make_text_value_with_units(self, *args, **kwargs):
        from workers.builder.text_value_with_units.text_value_with_units import BuilderTextValueWithUnitsCreator
        return BuilderTextValueWithUnitsCreator.make_text_value_with_units(self, *args, **kwargs)

    def make_text_web_link(self, *args, **kwargs):
        from workers.builder.text_web_link.text_web_link import BuilderTextWebLinkCreator
        return BuilderTextWebLinkCreator.make_text_web_link(self, *args, **kwargs)

    def make_images_image_display(self, *args, **kwargs):
        from workers.builder.images_image_display.images_image_display import BuilderImagesImageDisplayCreator
        return BuilderImagesImageDisplayCreator.make_images_image_display(self, *args, **kwargs)

    def make_images_animation_display(self, *args, **kwargs):
        from workers.builder.images_animation_display.images_animation_display import BuilderImagesAnimationDisplayCreator
        return BuilderImagesAnimationDisplayCreator.make_images_animation_display(self, *args, **kwargs)

    def make_data_json_tree(self, *args, **kwargs):
        from workers.builder.data_json_tree.data_json_tree import BuilderDataJsonTreeCreator
        return BuilderDataJsonTreeCreator.make_data_json_tree(self, *args, **kwargs)

    def make_meter_bar(self, *args, **kwargs):
        from workers.builder.meter_bar.meter_bar import BuilderMeterBarCreator
        return BuilderMeterBarCreator.make_meter_bar(*args, **kwargs)

    def make_knob_rotary_selector(self, *args, **kwargs):
        from workers.builder.knob_rotary_selector.knob_rotary_selector import BuilderKnobRotarySelectorCreator
        return BuilderKnobRotarySelectorCreator.make_knob_rotary_selector(self, *args, **kwargs)

    def make_input_inc_dec_buttons(self, *args, **kwargs):
        from workers.builder.input_inc_dec_buttons.input_inc_dec_buttons import BuilderInputIncDecButtonsCreator
        return BuilderInputIncDecButtonsCreator.make_input_inc_dec_buttons(self, *args, **kwargs)

    def make_input_directional_buttons(self, *args, **kwargs):
        from workers.builder.input_directional_buttons.input_directional_buttons import BuilderInputDirectionalButtonsCreator
        return BuilderInputDirectionalButtonsCreator.make_input_directional_buttons(self, *args, **kwargs)

    def make_fader_horizontal_dual(self, *args, **kwargs):
        from workers.builder.fader_horizontal_dual.fader_horizontal_dual import BuilderFaderHorizontalDualCreator
        return BuilderFaderHorizontalDualCreator.make_fader_horizontal_dual(self, *args, **kwargs)

    def make_button_trapezoid_toggler(self, *args, **kwargs):
        from workers.builder.button_trapezoid_toggler.button_trapezoid_toggler import BuilderButtonTrapezoidTogglerCreator
        return BuilderButtonTrapezoidTogglerCreator.make_button_trapezoid_toggler(self, *args, **kwargs)

    def make_button_wink(self, *args, **kwargs):
        from workers.builder.button_wink.button_wink import BuilderButtonWinkCreator
        return BuilderButtonWinkCreator.make_button_wink(self, *args, **kwargs)

    def make_button_wink_toggler(self, *args, **kwargs):
        from workers.builder.button_wink_toggler.button_wink_toggler import BuilderButtonWinkTogglerCreator
        return BuilderButtonWinkTogglerCreator.make_button_wink_toggler(self, *args, **kwargs)

    def make_meter_knob_with_vu_meter(self, *args, **kwargs):
        from workers.builder.meter_knob_with_vu_meter.meter_knob_with_vu_meter import BuilderMeterKnobWithVuMeterCreator
        return BuilderMeterKnobWithVuMeterCreator.make_meter_knob_with_vu_meter(self, *args, **kwargs)

    def make_data_radar(self, *args, **kwargs):
        from workers.builder.data_radar.data_radar import BuilderDataRadarCreator
        return BuilderDataRadarCreator.make_data_radar(self, *args, **kwargs)

    def make_fader_ganged_controlled_array(self, *args, **kwargs):
        from workers.builder.fader_ganged_controlled_array.fader_ganged_controlled_array import BuilderFaderGangedControlledArrayCreator
        return BuilderFaderGangedControlledArrayCreator.make_fader_ganged_controlled_array(self, *args, **kwargs)

    def make_fader_bar_graph(self, *args, **kwargs):
        from workers.builder.fader_bar_graph.fader_bar_graph import BuilderFaderBarGraphCreator
        return BuilderFaderBarGraphCreator.make_fader_bar_graph(self, *args, **kwargs)

    def make_composite_mdp(self, *args, **kwargs):
        from workers.builder.composite_mdp.composite_mdp import BuilderCompositeMdpCreator
        return BuilderCompositeMdpCreator.make_composite_mdp(self, *args, **kwargs)

    def make_circular_motion_displacement_potentiometer(self, *args, **kwargs):
        from workers.builder.circular_motion_displacement_potentiometer.circular_motion_displacement_potentiometer import BuilderCircularMotionDisplacementPotentiometerCreator
        return BuilderCircularMotionDisplacementPotentiometerCreator.make_circular_motion_displacement_potentiometer(self, *args, **kwargs)

    def _create_horizontal_meter(self, *args, **kwargs):
        from workers.builder.data_graphing.meter_widget_adapter import MeterWidgetAdapterMixin
        return MeterWidgetAdapterMixin._create_horizontal_meter(self, *args, **kwargs)

    def _create_vertical_meter(self, *args, **kwargs):
        from workers.builder.data_graphing.meter_widget_adapter import MeterWidgetAdapterMixin
        return MeterWidgetAdapterMixin._create_vertical_meter(self, *args, **kwargs)

    def _create_break_line(self, *args, **kwargs):
        from workers.builder.break_line.hidden_BreakLine import BreakLineCreatorMixin
        return BreakLineCreatorMixin._create_break_line(self, *args, **kwargs)

    def _create_collapsible_block(self, *args, **kwargs):
        from managers.Display.array.collapsible_block.collapsible_block import CollapsibleBlockCreatorMixin
        return CollapsibleBlockCreatorMixin._create_collapsible_block(self, *args, **kwargs)

    def _create_status_light(self, *args, **kwargs):
        from workers.builder.status_light.status_light import HeaderStatusLightMixin
        return HeaderStatusLightMixin._build_header_status_light(self, *args, **kwargs)
