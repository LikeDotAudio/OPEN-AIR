# meter_bar/meter_bar.py
# Author: Anthony Peter Kuzub
# Version: 20260223.Modernized.1
#
# Description: A modern bar-style meter widget with ballistics and peak hold.

import inspect

from oaGui.Core.factory.base_widget_creator import BaseWidgetCreator
from oaGui.Hooks.registry.registry_widget_store import RegistryWidgetStore
from oaGui.Methods.formatting.i18n_utils import get_text
from oaGui.Workers.compositing.engine_visual_effects import EngineVisualEffects
from oaGui.Workers.compositing.sync_behavior import SyncBehavior
from oaLogging.Core.logger import builder_logger
from oaLogging.Methods.matrix_gate import matrix_log

from .smart_meter import SmartMeter


@RegistryWidgetStore.register("_BarGraph", "_SmartMeter", "MeterBar", "_MeterBar")
class BuilderMeterBarCreator(BaseWidgetCreator, SyncBehavior):
    """Factory for creating Meter Bar widgets."""

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """
        Implementation of the Template Method for Meter Bar assembly.
        """
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔬🏗️📊 [BUILDER] Entering _assemble_ui", level="TRACE")

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
                apply_transparency_func=EngineVisualEffects.apply_transparency,
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
