# managers/VisaScipi/visa_writer.py
import orjson
import time

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()


def write_safe(proxy, command):
    # Safely writes a SCPI command to the instrument.
    if LOCAL_DEBUG: logger.debug(f"💳 ℹ️ Proxy Log: 💳💳⬆️⬆️ Send Visa Command: Transmitting command: {command}")

    if not proxy.inst:
        error_msg = "Instrument not connected. Cannot write command."
        proxy._publish_proxy_error(message=error_msg, command=command)
        proxy.mqtt_util.get_client_instance().publish(
            topic="OPEN-AIR/Proxy/Error",
            payload=orjson.dumps(
                {"error": error_msg, "command": command, "timestamp": time.time()}
            ),
            qos=0,
            retain=False,
        )
        return False

    if "<" in command or ">" in command:
        error_msg = f"Command rejected. Unresolved placeholders found: '{command}'."
        proxy._publish_proxy_error(message=error_msg, command=command)
        proxy.mqtt_util.get_client_instance().publish(
            topic="OPEN-AIR/Proxy/Error",
            payload=orjson.dumps(
                {"error": error_msg, "command": command, "timestamp": time.time()}
            ),
            qos=0,
            retain=False,
        )
        return False

    try:
        proxy.inst.write(command)
        if LOCAL_DEBUG: logger.success(f"💳 ℹ️ Proxy Log: ✅ Sent command: {command}")
        return True
    except Exception as e:
        error_msg = f"Error writing command '{command}': {e}"
        proxy._publish_proxy_error(message=error_msg, command=command)
        proxy.mqtt_util.get_client_instance().publish(
            topic="OPEN-AIR/Proxy/Error",
            payload=orjson.dumps(
                {"error": error_msg, "command": command, "timestamp": time.time()}
            ),
            qos=0,
            retain=False,
        )

        if command != "*RST":
            proxy._reset_device()
        return False