# managers/VisaScipi/visa_reader.py
import orjson
import time

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()


def query_safe(proxy, command, correlation_id="N/A"):
    # Safely queries the instrument with a SCPI command and returns the response.
    if LOCAL_DEBUG: logger.debug(f"💳 ℹ️ Proxy Log: 💳💳⬆️⬆️ Send Visa Command: Querying command: {command}")

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
    
    if LOCAL_DEBUG: logger.success(f"💳 ℹ️ Proxy Log: ✅ Sent query: {command}")
    if LOCAL_DEBUG: logger.debug(f"💳 ℹ️ Proxy Log: 💳💳⬇️⬇️ RX Visa Response: Received response: {response}")

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