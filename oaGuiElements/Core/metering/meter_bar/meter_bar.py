# meter_bar/meter_bar.py
# Author: Anthony Peter Kuzub
# Version: 20260223.Modernized.1
#
# Description: A modern bar-style meter widget with ballistics and peak hold.

from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from loguru import logger

from .smart_meter import SmartMeter
from oaGuiManager.Core.transparency.transparency import TransparencyManager
from oaGui.Methods.i18n_utils import get_text
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

@WidgetRegistry.register("_BarGraph", "_SmartMeter", "MeterBar", "_MeterBar")
class BuilderMeterBarCreator:
    """Factory for creating Meter Bar widgets."""

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """Static factory method for the registry."""
        return BuilderMeterBarCreator.make_meter_bar(
            parent_widget, config_data, context=context, **kwargs
        )

    @staticmethod
    def make_meter_bar(parent_widget, config_data, context=None, **kwargs):
        """Main entry point for creating a meter bar."""
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] Entering make_meter_bar", level="TRACE")
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📜📑💻 [CONFIG] Raw config received: {config_data}", level="DEBUG")
    
        label = get_text(config_data.get("label_active"), get_text(config_data.get('label'), "Unknown"))
        path = config_data.get("path")

        # ⚡ HARDENED INTERFACE: Extract from context if available
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...", level="TRACE")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.", level="DEBUG")
        else:
            state_mirror_engine = kwargs.get("state_mirror_engine")
            subscriber_router = kwargs.get("subscriber_router")
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance")
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "⚠️🔔🖱️ [CONTEXT] Context missing; fell back to kwargs.", level="DEBUG")

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬⚡️📊 [BUILDER] Instantiating SmartMeter for '{label}' at path '{path}'.", level="DEBUG")

        try:
            # 1. Instantiate the modular widget
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🏗️🪟🎨 [CONSTRUCT] Initializing SmartMeter modular core for '{label}'", level="TRACE")
            meter = SmartMeter(
                parent=parent_widget,
                raw_config=config_data,
                state_mirror_engine=state_mirror_engine,
                subscriber_router=subscriber_router,
                base_topic=base_mqtt_topic_from_path,
                builder_instance=builder_instance,
                # Pass transparency applicator
                apply_transparency_func=TransparencyManager.apply_transparency
            )

            # 2. Handle State Mirroring & MQTT Registration
            if path and state_mirror_engine:
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📡📶🔗 [MQTT] Registering meter bar at path '{path}'", level="TRACE")
                topic = state_mirror_engine.register_widget(
                    path, meter.value_var, base_mqtt_topic_from_path, config_data
                )
                if subscriber_router and topic:
                    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📥📶🔄 [MQTT] Subscribing to topic: {topic}", level="DEBUG")
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )
                
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔄⏳🔋 [STATE] Initializing widget state from cache/broker for '{path}'", level="TRACE")
                state_mirror_engine.initialize_widget_state(path)

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"✅🆗📊 [SUCCESS] The meter bar '{label}' has materialized!", level="SUCCESS")
            return meter

        except Exception as e:
            builder_logger.exception(f"❌🚫🛑 [ERROR] Critical failure building modular SmartMeter for '{label}': {e}")
            return None
