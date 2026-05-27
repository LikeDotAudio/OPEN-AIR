# oaGui/Managers/bootstrap/control_link_assembler.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for establishing internal system control links via MQTT.

def assemble_system_control_links(sub_router, splinker_manager):
    """Subscribes the splinker manager to its dedicated system control topic."""

    def _splinker_callback_bridge(message):
        splinker_manager.handle_mqtt_command(
            topic=message.topic,
            payload=message.payload
        )

    sub_router.subscribe_to_topic(
        topic_filter="OpenAir/System/Control/Splinker/#",
        callback_func=_splinker_callback_bridge
    )
