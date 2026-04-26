# oaGuiEditorWYSIWYG/Managers/runner/mqtt_tester.py
# Author: Anthony Peter Kuzub
# Version: 20260416.0230.1
#
# Description: MQTT Bridge for live-testing UI definitions in the main application.

import orjson

from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Core.logger import WYSIWYG_LOGGER
from oaLogging.Methods.matrix_gate import matrix_log

logger = WYSIWYG_LOGGER.bind(protocol="WYSIWYG")

class MqttTester:
    """Handles publishing test configurations to the main application via MQTT."""

    @staticmethod
    def publish_rebuild(json_filepath, new_data):
        """
        Triggers a live rebuild in the main application.
        Sends the current editor state over the 'Rebuild' topic.
        """
        matrix_log("ui", "gui_builder", "test", f"🚦 [PIPELINE] Standalone Builder: 'Test' triggered for {json_filepath.name}", "INFO")

        try:
            import paho.mqtt.client as mqtt
            app_config = Config.get_instance()

            # Connection parameters from global config
            broker = getattr(app_config, "MQTT_BROKER_ADDRESS", "localhost")
            port = getattr(app_config, "MQTT_BROKER_PORT", 1883)
            user = getattr(app_config, "MQTT_USERNAME", None)
            pw = getattr(app_config, "MQTT_PASSWORD", None)

            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            if user and pw:
                client.username_pw_set(user, pw)

            client.connect(broker, port, keepalive=10)

            # The topic OPEN-AIR listens to for design-time rebuilds
            rebuild_topic = "OPEN-AIR/System/Control/UI/Rebuild"
            payload = {
                "path": str(json_filepath.resolve()),
                "config": new_data
            }

            client.publish(rebuild_topic, orjson.dumps(payload))
            client.disconnect()

            matrix_log("ui", "gui_builder", "test", "✅ Standalone Builder: Rebuild request published to MQTT.", "SUCCESS")

        except ImportError:
            logger.error("Standalone Builder: 'paho-mqtt' library missing. Test functionality disabled.")
        except Exception as e:
            logger.error(f"Standalone Builder: MQTT Publish failed: {e}")
