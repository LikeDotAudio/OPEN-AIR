import inspect
import time

# Core/visa_safe_query.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose
import orjson

from oaConfigurationManager.FileReaders.config_reader import Config

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()


def query_safe(proxy, command, correlation_id="N/A"):
    # Safely queries the instrument with a SCPI command and returns the response.
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ Proxy Log: 💳💳⬆️⬆️ Send Visa Command: Querying command: {command}", "DEBUG")

    # ⚡ DEFENSIVE CHECK: Ensure session is still valid
    if not proxy.inst or not proxy.inst.session:
        error_message = "Instrument session lost. Cannot query command."
        proxy._publish_proxy_error(message=error_message, command=command)
        return None

    if "<" in command or ">" in command:
        error_message = f"Query rejected. Unresolved placeholders found: '{command}'."
        proxy._publish_proxy_error(message=error_message, command=command)
        # Assuming MQTT publish is safe or fatal
        proxy.mqtt_util.get_client_instance().publish(
            topic="OpenAir/Proxy/Error",
            payload=orjson.dumps(
                {"error": error_message, "command": command, "timestamp": time.time()}
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
        error_message = f"Timeout waiting for response to {command}"
        proxy._publish_proxy_error(message=error_message, command=command)
        proxy._reset_device()
        return None

    # ⚡ MEMORY GUARD: Monitor buffer size before reading
    buffer_size = proxy.inst.bytes_in_buffer
    if buffer_size > 1024 * 1024: # > 1MB
        matrix_log("comms", "visa", "query_safe",
                   f"⚠️ [MEMORY] Large instrument response detected: {buffer_size} bytes. "
                   f"Reading in bulk.", "WARNING")

    # Read the full response
    response = proxy.inst.read().strip()

    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ Proxy Log: ✅ Sent query: {command}", "SUCCESS")
    resp_str = str(response)[:100] + ("..." if len(str(response)) > 100 else "")
    matrix_log("comms", "visa", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💳 ℹ️ Proxy Log: 💳💳⬇️⬇️ RX Visa Response: Received response: {resp_str}", "DEBUG")

    topic = "OpenAir/Proxy/Rx_Outbox"
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
