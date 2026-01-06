# managers/Visa_Fleet_Manager/manager_visa_Search.py
#
# Dedicated module for probing VISA devices and parsing their identification.
#
# Author: Gemini Agent
#

import pyvisa
import time
import re
import string  # For _clean_string_for_display

try:
    from workers.logger.logger import debug_logger
    from workers.logger.log_utils import _get_log_args
except ModuleNotFoundError:
    print(
        "Warning: 'workers.logger' not found. Using dummy logger for manager_visa_Search."
    )

    def debug_logger(message, *args, **kwargs):
        if kwargs.get("level", "INFO") != "DEBUG":
            print(f"[{kwargs.get('level', 'INFO')}] {message}")

    def _get_log_args(*args, **kwargs):
        return {}  # Return empty dict, as logger args are not available


# --- CONFIGURATION (from cli_visa_find.py) ---
VISA_TIMEOUT = 5000


def _clean_string_for_display(s):
    if not s:
        return ""
    return "".join(filter(lambda x: x in string.printable, s)).strip()


def _parse_idn(idn_str):
    if not idn_str:
        return ("Unknown", "Unknown", "", "")
    parts = idn_str.split(",")
    while len(parts) < 4:
        parts.append("")
    return (parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip())


def _parse_resource_details(res_str):
    details = {"IP": "Unknown", "Interface": "Unknown", "GPIB_Addr": "N/A"}
    clean_res = _clean_string_for_display(res_str)
    parts = clean_res.split("::")

    if clean_res.startswith("TCPIP"):
        if len(parts) >= 2:
            details["IP"] = parts[1]
            if len(parts) > 2 and "," in parts[2]:
                sub_parts = parts[2].split(",")
                details["Interface"] = sub_parts[0]
                details["GPIB_Addr"] = ",".join(sub_parts[1:])
            else:
                details["Interface"] = "Ethernet"
                details["GPIB_Addr"] = "Direct"
    elif clean_res.startswith("USB"):
        details["Interface"] = "USB"
        details["IP"] = "USB"
        details["GPIB_Addr"] = "Direct"
    return details


def _query_device_safe(rm, resource_str, attempt=1):
    inst = None
    try:
        inst = rm.open_resource(resource_str)
        inst.timeout = VISA_TIMEOUT
        inst.read_termination = "\n"
        inst.write_termination = "\n"

        # Explicitly log the raw IDN response for debugging
        raw_idn = inst.query("*IDN?")
        idn = _clean_string_for_display(raw_idn)

        debug_logger(
            f"      Raw IDN for {resource_str}: '{raw_idn}'",
            **_get_log_args(),
            level="DEBUG",
        )
        debug_logger(
            f"      Cleaned IDN for {resource_str}: '{idn}'",
            **_get_log_args(),
            level="DEBUG",
        )

        inst.close()

        if not idn:  # If IDN is empty after cleaning
            debug_logger(
                f"      Empty IDN received for {resource_str}.",
                **_get_log_args(),
                level="WARNING",
            )
            return None  # Treat empty IDN as failure to probe
        return idn
    except pyvisa.errors.VisaIOError as vioe:
        debug_logger(
            f"      ❌ VISA IO Error during IDN query for {resource_str}: {vioe}",
            **_get_log_args(),
            level="ERROR",
        )
        if inst:
            try:
                inst.close()
            except:
                pass
        if attempt == 1 and ("USB" in resource_str or "ASRL" in resource_str):
            time.sleep(2.0)
            return _query_device_safe(rm, resource_str, attempt=2)
        return None
    except Exception as e:
        debug_logger(
            f"      ❌ Unexpected Error during IDN query for {resource_str}: {e}",
            **_get_log_args(),
            level="ERROR",
        )
        if inst:
            try:
                inst.close()
            except:
                pass
        if attempt == 1 and ("USB" in resource_str or "ASRL" in resource_str):
            time.sleep(2.0)
            return _query_device_safe(rm, resource_str, attempt=2)
        return None


def probe_devices(resource_manager, potential_targets):
    """
    Probes a list of potential VISA resources to gather detailed information.

    Args:
        resource_manager: The PyVISA ResourceManager instance.
        potential_targets (list): A list of dictionaries, each with 'Type' and 'Resource' keys.
                                  E.g., [{"Type": "DEDICATED", "Resource": "TCPIP::192.168.1.10::INSTR"}]

    Returns:
        dict: A dictionary of probed device entries, keyed by device identifier (serial number or sanitized resource).
    """
    debug_logger(
        f"💳 🔍 manager_visa_Search: Received {len(potential_targets)} potential targets for probing: {potential_targets}",
        **_get_log_args(),
    )
    device_collection = {}

    try:
        for idx, target in enumerate(potential_targets):
            raw_res = target["Resource"]
            display_res = _clean_string_for_display(raw_res)

            debug_logger(
                f"   🎯 Probing {display_res} ... ",
                **_get_log_args(),
                end="",
                flush=True,
            )

            conn_details = _parse_resource_details(display_res)
            idn = _query_device_safe(resource_manager, raw_res)

            device_entry = {
                # "id": str(idx + 1), # Will be replaced by serial or similar unique ID
                "type": target["Type"],
                "resource_string": display_res,
                "ip_address": conn_details["IP"],
                "interface_port": conn_details["Interface"],
                "gpib_address": conn_details["GPIB_Addr"],
            }

            if idn:
                debug_logger(f"SUCCESS", **_get_log_args())
                mfg, model, serial_num, firm = _parse_idn(
                    idn
                )  # Use _parse_idn for basic parsing

                device_identifier = serial_num
                if not device_identifier or device_identifier == "0":
                    # Construct unique ID from IP last octet, interface port number, and GPIB address
                    # Example: "222-7-1" from IP 44.44.44.222, gpib7, 1

                    last_octet = "Unknown"
                    if conn_details["IP"] and "." in conn_details["IP"]:
                        last_octet = conn_details["IP"].split(".")[-1]
                    elif conn_details["IP"] == "USB":  # Handle USB IP
                        last_octet = "USB"

                    interface_port_num = "Unknown"
                    if conn_details["Interface"]:
                        match = re.search(r"\d+", conn_details["Interface"])
                        if match:
                            interface_port_num = match.group(0)
                        else:
                            interface_port_num = conn_details[
                                "Interface"
                            ]  # Use full string if no number

                    gpib_addr = (
                        conn_details["GPIB_Addr"]
                        if conn_details["GPIB_Addr"] != "N/A"
                        else "Unknown"
                    )

                    # Combine to form the new device_identifier
                    # Sanitize components to ensure valid identifier (e.g., replace non-alphanumeric with '_')
                    device_identifier_parts = [
                        last_octet,
                        interface_port_num,
                        gpib_addr,
                    ]
                    sanitized_parts = [
                        re.sub(r"[^\w\-]+", "_", str(p))
                        for p in device_identifier_parts
                    ]

                    device_identifier = "-".join(sanitized_parts)

                    debug_logger(
                        f"      Generated new device_identifier for empty/0 serial: {device_identifier}",
                        **_get_log_args(),
                        level="DEBUG",
                    )

                # Ensure the device_identifier is unique across the collection
                original_identifier = device_identifier
                counter = 1
                while device_identifier in device_collection:
                    device_identifier = f"{original_identifier}_{counter}"
                    counter += 1

                device_entry.update(
                    {
                        "status": "Active",
                        "manufacturer": mfg,
                        "model": model,
                        "serial_number": serial_num,
                        "firmware": firm,
                        "idn_string": idn,
                        # "idn_details": {} # Will be added by supervisor with robust parser
                    }
                )
            else:
                debug_logger(
                    f"FAILED (IDN Query Error)", **_get_log_args(), level="ERROR"
                )
                device_identifier = re.sub(
                    r"[^\w\-]+", "_", raw_res
                )  # Still need identifier for unresponsive devices
                device_entry.update(
                    {
                        "status": "Unresponsive",
                        "manufacturer": "Unknown",
                        "model": "Unknown",
                        "serial_number": "Unknown",
                        "firmware": "Unknown",
                        "device_type": "Unknown",
                        "notes": "Connection Timed Out",
                    }
                )

            device_collection[device_identifier] = device_entry
    except Exception as e:
        debug_logger(
            f"💳 🔍 CRITICAL manager_visa_Search: Exception in probe_devices loop: {e}",
            **_get_log_args(),
            level="ERROR",
        )

    debug_logger(
        f"💳 🔍 manager_visa_Search: Finished probing. Returning {len(device_collection)} probed devices: {device_collection}",
        **_get_log_args(),
    )
    return device_collection


# For testing purposes (optional)
if __name__ == "__main__":
    rm = pyvisa.ResourceManager("@py")
    # Example potential targets (replace with real data for testing)
    example_targets = [
        {"Type": "LOCAL", "Resource": "USB0::0x1234::0x5678::SN12345::INSTR"},
        {"Type": "DEDICATED", "Resource": "TCPIP::192.168.1.10::INSTR"},
    ]
    probed_devices = probe_devices(rm, example_targets)
    print("\nProbed Devices:")
    for dev_id, dev_data in probed_devices.items():
        print(f"  {dev_id}: {dev_data}")
