# managers/VisaScipi/visa_reader.py
import orjson
import time
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args


def query_safe(proxy, command, correlation_id="N/A"):
    # Safely queries the instrument with a SCPI command and returns the response.
    debug_logger(
        message=f"💳 ℹ️ Proxy Log: 💳💳⬆️⬆️ Send Visa Command: Querying command: {command}",
        **_get_log_args(),
    )

    if not proxy.inst:
        error_msg = "Instrument not connected. Cannot query command."
        proxy._publish_proxy_error(message=error_msg, command=command)
        proxy.mqtt_util.get_client_instance().publish(
            topic="OPEN-AIR/Proxy/Error",
            payload=orjson.dumps(
                {"error": error_msg, "command": command, "timestamp": time.time()}
            ),
            qos=0,
            retain=False,
        )
        return None

    if "<" in command or ">" in command:
        error_msg = f"Query rejected. Unresolved placeholders found: '{command}'."
        proxy._publish_proxy_error(message=error_msg, command=command)
        proxy.mqtt_util.get_client_instance().publish(
            topic="OPEN-AIR/Proxy/Error",
            payload=orjson.dumps(
                {"error": error_msg, "command": command, "timestamp": time.time()}
            ),
            qos=0,
            retain=False,
        )
        return None

    try:
        response = proxy.inst.query(command).strip()
        debug_logger(
            message=f"💳 ℹ️ Proxy Log: ✅ Sent query: {command}", **_get_log_args()
        )
        debug_logger(
            message=f"💳 ℹ️ Proxy Log: 💳💳⬇️⬇️ RX Visa Response: Received response: {response}",
            **_get_log_args(),
        )

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
    except Exception as e:
        error_msg = f"Error querying command '{command}': {e}"
        proxy._publish_proxy_error(message=error_msg, command=command)
        proxy.mqtt_util.get_client_instance().publish(
            topic="OPEN-AIR/Proxy/Error",
            payload=orjson.dumps(
                {"error": error_msg, "command": command, "timestamp": time.time()}
            ),
            qos=0,
            retain=False,
        )
        proxy._reset_device()
        return None
