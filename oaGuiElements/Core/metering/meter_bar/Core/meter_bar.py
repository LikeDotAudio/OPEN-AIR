# meter_bar/meter_bar.py
# Author: Anthony Peter Kuzub
# Version: 20260223.Modernized.1
#
# Description: A modern bar-style meter widget with ballistics and peak hold.

from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import tkinter as tk
from loguru import logger

from .smart_meter import SmartMeter
from oaGuiManager.Core.transparency.transparency import TransparencyManager
from oaGui.Methods.i18n_utils import get_text
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry
from oaGuiBuilder.Core.base_widget_creator import BaseWidgetCreator
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

@WidgetRegistry.register("_BarGraph", "_SmartMeter", "MeterBar", "_MeterBar")
class BuilderMeterBarCreator(BaseWidgetCreator, TransparencyMixin):
    """Factory for creating Meter Bar widgets."""

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """
        Implementation of the Template Method for Meter Bar assembly.
        """
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] Entering _assemble_ui", level="TRACE")
    
        label = get_text(config_data.get("label_active"), get_text(config_data.get('label'), "Unknown"))
        
        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = getattr(ctx, 'builder_instance', None) or getattr(ctx, 'app_instance', None) or kwargs.get('builder_instance')
        s_engine = getattr(ctx, 'state_mirror_engine', None) or kwargs.get('state_mirror_engine')
        s_router = getattr(ctx, 'subscriber_router', None) or kwargs.get('subscriber_router')
        b_topic = getattr(ctx, 'base_mqtt_topic_from_path', None) or kwargs.get('base_mqtt_topic_from_path')

        try:
            # 1. Instantiate the modular widget
            meter = SmartMeter(
                parent=parent_widget,
                raw_config=config_data,
                state_mirror_engine=s_engine,
                subscriber_router=s_router,
                base_topic=b_topic,
                builder_instance=b_inst,
                # Pass transparency applicator (though BaseWidgetCreator will also handle it)
                apply_transparency_func=TransparencyManager.apply_transparency,
                variable=kwargs.get("variable")
            )
            
            # Link variable for BaseWidgetCreator registration
            meter.variable = meter.value_var

            return meter, getattr(meter, 'canvas', meter)

        except Exception as e:
            builder_logger.exception(f"❌🚫🛑 [ERROR] Critical failure building modular SmartMeter for '{label}': {e}")
            return None, None

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """Static factory method for the registry."""
        return BuilderMeterBarCreator.build(parent_widget, config_data, context, **kwargs)

    def make_meter_bar(self, parent_widget, config_data, context=None, **kwargs):
        """Main entry point for creating a meter bar."""
        return self.build(parent_widget, config_data, context, **kwargs)
