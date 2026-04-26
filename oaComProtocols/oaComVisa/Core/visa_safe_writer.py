import inspect
import time

# Core/visa_safe_writer.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose
import orjson

from oaConfigurationManager.FileReaders.config_reader import Config

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()


def write_safe(proxy, command):
    # Safely writes a SCPI command to the instrument.
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ Proxy Log: 💳💳⬆️⬆️ Send Visa Command: Transmitting command: {command}", "DEBUG")

    # ⚡ DEFENSIVE CHECK: Ensure session is still valid
    if not proxy.inst or not proxy.inst.session:
        error_message = "Instrument session lost. Cannot write command."
        proxy._publish_proxy_error(message=error_message, command=command)
        return False

    if "<" in command or ">" in command:
        error_message = f"Command rejected. Unresolved placeholders found: '{command}'."
        proxy._publish_proxy_error(message=error_message, command=command)
        proxy.mqtt_util.get_client_instance().publish(
            topic="OPEN-AIR/Proxy/Error",
            payload=orjson.dumps(
                {"error": error_message, "command": command, "timestamp": time.time()}
            ),
            qos=0,
            retain=False,
        )
        return False

    # ⚡ DIRECT CALL: Assuming hardware state is validated or fatal if not
    proxy.inst.write(command)
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ Proxy Log: ✅ Sent command: {command}", "SUCCESS")
    return True
