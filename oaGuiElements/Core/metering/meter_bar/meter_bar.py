# workers/builder/meter_bar/meter_bar.py
#
# A modern bar-style meter widget with ballistics and peak hold.
# Renamed from bar_graph to meter_bar.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260223.Modernized.1

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from .smart_meter import SmartMeter
from oaGuiManager.Core.transparency.transparency import TransparencyManager
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
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️📊 [BUILDER] Entering make_meter_bar")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")
        
        label = config_data.get("label_active", config_data.get("label", "Unknown"))
        path = config_data.get("path")

        # ⚡ HARDENED INTERFACE: Extract from context if available
        if BUILDER_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
            if BUILDER_DEBUG: builder_logger.debug("✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.")
        else:
            state_mirror_engine = kwargs.get("state_mirror_engine")
            subscriber_router = kwargs.get("subscriber_router")
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance")
            if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to kwargs.")

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️📊 [BUILDER] Instantiating SmartMeter for '{label}' at path '{path}'.")

        try:
            # 1. Instantiate the modular widget
            if BUILDER_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [CONSTRUCT] Initializing SmartMeter modular core for '{label}'")
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
                if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering meter bar at path '{path}'")
                topic = state_mirror_engine.register_widget(
                    path, meter.value_var, base_mqtt_topic_from_path, config_data
                )
                if subscriber_router and topic:
                    if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing to topic: {topic}")
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )
                
                if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing widget state from cache/broker for '{path}'")
                state_mirror_engine.initialize_widget_state(path)

            if BUILDER_DEBUG: builder_logger.success(f"✅🆗📊 [SUCCESS] The meter bar '{label}' has materialized!")
            return meter

        except Exception as e:
            if BUILDER_DEBUG:
                builder_logger.exception(f"❌🚫🛑 [ERROR] Critical failure building modular SmartMeter for '{label}'")
            return None
