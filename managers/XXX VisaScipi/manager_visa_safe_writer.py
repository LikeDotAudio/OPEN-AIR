# managers/VisaScipi/visa_writer.py
import orjson
import time
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args


def write_safe(proxy, command):
    # Safely writes a SCPI command to the instrument.
    debug_logger(
        message=f"💳 ℹ️ Proxy Log: 💳💳⬆️⬆️ Send Visa Command: Transmitting command: {command}",
        **_get_log_args(),
    )

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
        debug_logger(
            message=f"💳 ℹ️ Proxy Log: ✅ Sent command: {command}", **_get_log_args()
        )
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
