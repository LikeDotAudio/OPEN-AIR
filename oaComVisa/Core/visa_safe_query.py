import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Core/visa_safe_query.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import orjson
import time

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()


def query_safe(proxy, command, correlation_id="N/A"):
    # Safely queries the instrument with a SCPI command and returns the response.
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ Proxy Log: 💳💳⬆️⬆️ Send Visa Command: Querying command: {command}", "DEBUG")

    # ⚡ DEFENSIVE CHECK: Ensure session is still valid
    if not proxy.inst or not proxy.inst.session:
        error_msg = "Instrument session lost. Cannot query command."
        proxy._publish_proxy_error(message=error_msg, command=command)
        return None

    if "<" in command or ">" in command:
        error_msg = f"Query rejected. Unresolved placeholders found: '{command}'."
        proxy._publish_proxy_error(message=error_msg, command=command)
        # Assuming MQTT publish is safe or fatal
        proxy.mqtt_util.get_client_instance().publish(
            topic="OPEN-AIR/Proxy/Error",
            payload=orjson.dumps(
                {"error": error_msg, "command": command, "timestamp": time.time()}
            ),
            qos=0,
            retain=False,
        )
        return None

    # ⚡ DIRECT CALL: Split query into write + polling read for Zero Exception
    proxy.inst.write(command)
    
    # Wait for data to arrive in buffer
    start_wait = time.time()
    while proxy.inst.bytes_in_buffer == 0 and (time.time() - start_wait) < (proxy.inst.timeout / 1000.0):
        time.sleep(0.01)
    
    if proxy.inst.bytes_in_buffer == 0:
        error_msg = f"Timeout waiting for response to {command}"
        proxy._publish_proxy_error(message=error_msg, command=command)
        proxy._reset_device()
        return None

    response = proxy.inst.read().strip()
    
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ Proxy Log: ✅ Sent query: {command}", "SUCCESS")
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ Proxy Log: 💳💳⬇️⬇️ RX Visa Response: Received response: {response}", "DEBUG")

    topic = "OPEN-AIR/Proxy/Rx_Outbox"
    payload = orjson.dumps(
        {
            "response": response,
            "command": command,
            "correlation_id": correlation_id,
            "timestamp": time.time(),
        }
    )
    proxy.mqtt_util.get_client_instance().publish(
        topic=topic, payload=payload, qos=0, retain=False
    )
    proxy._publish_proxy_response(
        response=response, command=command, correlation_id=correlation_id
    )
    return response
