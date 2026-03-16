# # managers/manager_presets_span.py
# #
# # This file (manager_presets_span.py) manages span preset buttons and publishes the selected value to the main span frequency control.
# # A complete and comprehensive pre-amble that describes the file and the functions within.
# # The purpose is to provide clear documentation and versioning.
# #
# # The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# # As the current hour is 20, no change is needed.
# 
# # Author: Anthony Peter Kuzub
# # Blog: www.Like.audio (Contributor to this project)
# #
# # Professional services for customizing and tailoring this software to your specific
# # application can be negotiated. There is no charge to use, modify, or fork this software.
# #
# # Build Log: https://like.audio/category/software/spectrum-scanner/
# # Source Code: https://github.com/APKaudio/
# # Feature Requests can be emailed to i @ like . audio
# #
# 
# 
# import os
# import inspect
# import orjson
# import pathlib
# 
# # Assume these are imported from a central logging utility and MQTT controller
# from workers.logger.logger import initialize_logging, set_log_directory
# from loguru import logger
# 
# 
# from workers.Command_Router.mqtt.mqtt_controller_util import MqttControllerUtility
# 
# LOCAL_DEBUG = True   
# 
# 
# class SpanSettingsManager:
#     """
#     Manages the logic for span presets.
#     """
# 
#     def __init__(self, mqtt_controller: MqttControllerUtility):
#         # Initializes the manager and subscribes to relevant topics.
#         current_function_name = inspect.currentframe().f_code.co_name
# 
#         self.mqtt_controller = mqtt_controller
#         self.base_topic = "OPEN-AIR/configuration/instrument/frequency"
#         self.span_presets_topic = f"{self.base_topic}/Presets/fields/SPAN/options"
#         self.target_span_topic = (
#             f"{self.base_topic}/Settings/fields/span_freq_MHz/value"
#         )
# 
#         # Dictionary to store preset values dynamically
#         self.preset_values = {}
# 
#         if LOCAL_DEBUG:
#             logger.debug(f"🟢️️️🟢 Initializing SpanSettingsManager and setting up subscriptions.")
# 
#         self._load_preset_values()
#         self._subscribe_to_topics()
# 
#     def _load_preset_values(self):
#         """
#         Loads the preset values directly from the configuration file.
#         This makes the manager self-sufficient and prevents timing issues.
#         """
#         try:
#             # FIX: Replaced fragile os.path.join with a robust pathlib implementation.
#             project_root = pathlib.Path(__file__).resolve().parents[2]
#             config_file_path = (
#                 project_root
#                 / "datasets"
#                 / "configuration"
#                 / "dataset_configuration_instrument_frequency.json"
#             )
# 
#             if not config_file_path.is_file():
#                 if LOCAL_DEBUG:
#                     logger.error(f"❌ Configuration file not found at '{config_file_path}'. Cannot load presets.")
#                 return
# 
#             with open(config_file_path, "r") as f:
#                 config_data = orjson.loads(f)
# 
#             span_options = (
#                 config_data.get("Presets", {})
#                 .get("fields", {})
#                 .get("SPAN", {})
#                 .get("options", {})
#             )
#             for key, option in span_options.items():
#                 self.preset_values[int(key)] = float(option.get("value"))
# 
#             if LOCAL_DEBUG:
#                 logger.success(f"💾 Successfully loaded {len(self.preset_values)} span preset values.")
# 
#         except Exception as e:
#             if LOCAL_DEBUG:
#                 logger.exception("🟢️️️🔴 Failed to load preset values from file. The error be")
# 
#     def _subscribe_to_topics(self):
#         # Subscribes to the preset topics.
#         current_function_name = inspect.currentframe().f_code.co_name
# 
#         # Subscribe only to the 'selected' topics, as we no longer need the 'value' topics.
#         for i in range(1, 8):
#             self.mqtt_controller.add_subscriber(
#                 topic_filter=f"{self.span_presets_topic}/{i}/selected",
#                 callback_func=self._on_preset_message,
#             )
# 
#             if LOCAL_DEBUG:
#                 logger.debug(f"🔍 Subscribed to span preset topics for option {i}.")
# 
#     def _on_preset_message(self, topic, payload):
#         # The main message processing callback for presets.
#         current_function_name = inspect.currentframe().f_code.co_name
# 
#         try:
#             parsed_payload = orjson.loads(payload)
#             value = parsed_payload.get("value", payload)
# 
#             if topic.endswith("/selected") and str(value).lower() == "true":
#                 self._update_span_from_preset(topic=topic)
# 
#             if LOCAL_DEBUG: logger.success("✅ The span settings did synchronize!")
# 
#         except Exception as e:
#             logger.exception("❌ Error in {current_function_name}")
#             if LOCAL_DEBUG:
#                 logger.exception("🟢️️️🔴 Arrr, the code be capsized! The span preset logic has failed! The error be")
# 
#     def _update_span_from_preset(self, topic):
#         # Extracts the value from the preset topic and updates the main span topic.
#         current_function_name = inspect.currentframe().f_code.co_name
# 
#         try:
#             option_number = int(topic.split("/")[-2])
#             new_span_value = self.preset_values.get(option_number)
# 
#             if new_span_value is not None:
#                 self._publish_update(topic=self.target_span_topic, value=new_span_value)
#                 if LOCAL_DEBUG:
#                     logger.debug(f"🔁 Preset selected! Published new span value to '{self.target_span_topic}'.")
#             else:
#                 if LOCAL_DEBUG:
#                     logger.debug(f"🟡 Warning: Preset value for option {option_number} has not been received yet.")
# 
#         except Exception as e:
#             if LOCAL_DEBUG:
#                 logger.exception("🟢️️️🔴 Failed to apply preset from topic '{topic}'. The error be")
# 
#     def _publish_update(self, topic, value):
#         # Publishes a message to the specified topic.
#         current_function_name = inspect.currentframe().f_code.co_name
# 
#         rounded_value = round(value, 3)
# 
#         if LOCAL_DEBUG:
#             logger.debug(f"💾 Publishing new value '{rounded_value}' to topic '{topic}'.")
# 
#         self.mqtt_controller.publish_message(
#             topic=topic, subtopic="", value=rounded_value, retain=False
#         )
