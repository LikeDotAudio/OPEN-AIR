# Hooks/mqtt_command_transmitter.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Handles formatting and publishing of GUI commands to MQTT.

import time
import orjson

class MqttCommandTransmitter:
    """Handles formatting and publishing of GUI commands to MQTT."""
    @staticmethod
    def transmit(builder, widget_name, value):
        """Centralized method for sending GUI updates to MQTT."""
        engine = builder.state_mirror_engine
        if not engine: return

        if hasattr(builder, '_log_command_tx'):
            builder._log_command_tx(f"{widget_name} -> {value}")

        if engine.is_widget_registered(widget_name):
            engine.broadcast_gui_change_to_mqtt(widget_name)
        else:
            topic = engine.calculate_topic(widget_name, builder.base_mqtt_topic_from_path)
            payload = {
                "value": value,
                "source": "gui",
                "timestamp": time.time(),
                "GUID": engine.GUID,
            }
            engine.publish_command(topic, orjson.dumps(payload).decode())

    @staticmethod
    def publish_init_state(builder, json_data):
        """Announces the GUI's initial configuration to MQTT."""
        engine = builder.state_mirror_engine
        if not engine: return

        payload = {
            "value": json_data,
            "source": "GUI-INIT",
            "timestamp": time.time(),
            "GUID": engine.GUID,
        }
        full_topic = engine.calculate_topic("", builder.base_mqtt_topic_from_path)
        engine.publish_command(full_topic, orjson.dumps(payload).decode())
