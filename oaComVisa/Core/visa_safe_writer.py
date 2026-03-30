# Core/visa_safe_writer.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import orjson
import time

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()


def write_safe(proxy, command):
    # Safely writes a SCPI command to the instrument.
    if LOCAL_DEBUG: logger.debug(f"💳 ℹ️ Proxy Log: 💳💳⬆️⬆️ Send Visa Command: Transmitting command: {command}")

    # ⚡ DEFENSIVE CHECK: Ensure session is still valid
    if not proxy.inst or not proxy.inst.session:
        error_msg = "Instrument session lost. Cannot write command."
        proxy._publish_proxy_error(message=error_msg, command=command)
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

    # ⚡ DIRECT CALL: Assuming hardware state is validated or fatal if not
    proxy.inst.write(command)
    if LOCAL_DEBUG: logger.success(f"💳 ℹ️ Proxy Log: ✅ Sent command: {command}")
    return True
