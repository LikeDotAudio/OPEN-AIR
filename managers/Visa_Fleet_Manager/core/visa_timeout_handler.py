from loguru import logger

def visa_timeout_handler(proxy_instance, command, exception):
    """
    Dedicated handler for VISA I/O timeouts and connection errors.
    Decides the recovery path for the specific instrument.
    """
    serial = proxy_instance.device_serial
    logger.error(f"💳🚢🚫 [VISA TIMEOUT] Device {serial} failed on command: {command}")
    logger.error(f"  └─ Reason: {exception}")

    error_msg = f"VISA I/O Error: {exception}"
    proxy_instance.manager._notify_error(
        serial=serial, message=error_msg, command=command
    )

    # Recovery Strategy: Mark offline and attempt a reset if appropriate
    proxy_instance.is_connected = False
    proxy_instance.manager._notify_status(serial=serial, status="OFFLINE")

    if command.strip().upper() not in ["*RST", ":SYSTem:POWer:RESe"]:
        logger.warning(f"💳🚢🔄 [RECOVERY] Attempting device-level reset for {serial}")
        proxy_instance._reset_device_fleet()
    
    return None
