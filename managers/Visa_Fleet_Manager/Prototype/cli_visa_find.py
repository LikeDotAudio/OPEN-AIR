import pyvisa
import urllib.request
import urllib.parse
import re
import json
import sys
import os
import string
import time
import socket
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
OUTPUT_FILENAME = "fleet_inventory.json"
HTTP_TIMEOUT = 5
VISA_TIMEOUT = 5000

# --- KNOWLEDGE BASE ---
# Maps Model Number -> {Type, Notes}
KNOWN_DEVICES = {
    "33220A": {"type": "Function Generator", "notes": "20 MHz Arbitrary Waveform"},
    "33210A": {"type": "Function Generator", "notes": "10 MHz Arbitrary Waveform"},
    "34401A": {"type": "Multimeter (DMM)", "notes": "6.5 Digit Benchtop Standard"},
    "54641D": {"type": "Oscilloscope", "notes": "Mixed Signal (2 Ana + 16 Dig)"},
    "DS1104Z": {"type": "Oscilloscope", "notes": "100 MHz, 4 Channel Digital"},
    "66000A": {"type": "Power Mainframe", "notes": "Modular System (8 Slots)"},
    "66101A": {"type": "DC Power Module", "notes": "8V / 16A (128W)"},
    "66102A": {"type": "DC Power Module", "notes": "20V / 7.5A (150W)"},
    "66103A": {"type": "DC Power Module", "notes": "35V / 4.5A (150W)"},
    "66104A": {"type": "DC Power Module", "notes": "60V / 2.5A (150W)"},
    "6060B": {"type": "Electronic Load", "notes": "DC Load (300 Watt)"},
    "3235": {"type": "Switch Unit", "notes": "High-perf Switching Matrix"},
    "3235A": {"type": "Switch Unit", "notes": "High-perf Switching Matrix"},
    "N9340B": {"type": "Spectrum Analyzer", "notes": "Handheld (100 kHz - 3 GHz)"},
}
# ---------------------


def clean_string_for_display(s):
    if not s:
        return ""
    return "".join(filter(lambda x: x in string.printable, s)).strip()


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


def check_host(ip):
    """Checks for Port 111 (Gateway) and Port 5025 (SCPI)."""
    # 1. Port 111 (VXI-11)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        result = sock.connect_ex((ip, 111))
        sock.close()
        if result == 0:
            is_gateway = False
            try:
                url = f"http://{ip}/html/instrumentspage.html"
                with urllib.request.urlopen(url, timeout=1) as resp:
                    if "E5810" in resp.read().decode("utf-8", errors="ignore"):
                        is_gateway = True
            except:
                pass
            return (ip, "GATEWAY" if is_gateway else "DEDICATED")
    except:
        pass

    # 2. Port 5025 (SCPI)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        result = sock.connect_ex((ip, 5025))
        sock.close()
        if result == 0:
            return (ip, "DEDICATED")
    except:
        pass
    return None


def hunt_for_devices():
    my_ip = get_local_ip()
    if my_ip == "127.0.0.1":
        return [], []
    subnet = ".".join(my_ip.split(".")[:-1])

    targets_to_scan = [
        f"{subnet}.{i}" for i in range(1, 255) if f"{subnet}.{i}" != my_ip
    ]

    gateways = []
    dedicated = []

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(check_host, ip): ip for ip in targets_to_scan}
        for future in futures:
            res = future.result()
            if res:
                ip, type_ = res
                if type_ == "GATEWAY":
                    gateways.append(ip)
                else:
                    dedicated.append(ip)
    return dedicated, gateways


def parse_idn(idn_str):
    if not idn_str:
        return ("Unknown", "Unknown", "", "")
    parts = idn_str.split(",")
    while len(parts) < 4:
        parts.append("")
    return (parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip())


def augment_device_details(device_entry):
    """
    Looks up the Model Number in KNOWN_DEVICES and adds Type/Notes to the entry.
    """
    model = device_entry.get("model", "Unknown")

    # Default values
    device_entry["device_type"] = "Unknown Instrument"
    device_entry["notes"] = "Not in Knowledge Base"

    if model in KNOWN_DEVICES:
        info = KNOWN_DEVICES[model]
        device_entry["device_type"] = info["type"]
        device_entry["notes"] = info["notes"]

    return device_entry


def parse_resource_details(res_str):
    details = {"IP": "Unknown", "Interface": "Unknown", "GPIB_Addr": "N/A"}
    clean_res = clean_string_for_display(res_str)
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


def get_gateway_inventory(ip):
    url = f"http://{ip}/html/instrumentspage.html"
    params = {"whichbutton": "find", "timeout": "5"}
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    targets = []
    try:
        with urllib.request.urlopen(full_url, timeout=HTTP_TIMEOUT) as response:
            html = response.read().decode("utf-8", errors="ignore")
            matches = re.findall(
                r"<option[^>]*>[\s\n]*([a-zA-Z0-9,]+)", html, re.IGNORECASE
            )
            for m in matches:
                m = m.strip()
                if "COM" not in m:
                    targets.append(m)
    except Exception:
        pass
    return targets


def query_device_safe(rm, resource_str, attempt=1):
    inst = None
    try:
        inst = rm.open_resource(resource_str)
        inst.timeout = VISA_TIMEOUT
        inst.read_termination = "\n"
        inst.write_termination = "\n"
        idn = inst.query("*IDN?").strip()
        inst.close()
        return clean_string_for_display(idn)
    except Exception:
        if inst:
            try:
                inst.close()
            except:
                pass
        if attempt == 1 and ("USB" in resource_str or "ASRL" in resource_str):
            time.sleep(2.0)
            return query_device_safe(rm, resource_str, attempt=2)
        return None


def main():
    print(f"--- VISA FLEET MANAGER (V14: KNOWLEDGE BASE) ---")

    potential_targets = []
    try:
        rm = pyvisa.ResourceManager("@py")
    except:
        rm = pyvisa.ResourceManager()

    # 1. HUNT
    print(f"\n[1/4] HUNTING NETWORK...")
    dedicated_ips, gateway_ips = hunt_for_devices()

    if dedicated_ips:
        print(f"   ✅ Found Dedicated: {dedicated_ips}")
    if gateway_ips:
        print(f"   ✅ Found Gateways: {gateway_ips}")
    if not dedicated_ips and not gateway_ips:
        print(f"   ⚪ No network devices found.")

    # 2. ENUMERATE
    print(f"\n[2/4] ENUMERATING TARGETS...")

    # A. Dedicated
    for ip in dedicated_ips:
        res = f"TCPIP::{ip}::INSTR"
        potential_targets.append({"Type": "DEDICATED", "Resource": res})

    # B. Gateways
    for ip in gateway_ips:
        print(f"   👉 Scraping Gateway {ip}...", end="", flush=True)
        targets = get_gateway_inventory(ip)
        print(f" Found {len(targets)}.")
        for t in targets:
            visa_res = f"TCPIP::{ip}::{t}::INSTR"
            potential_targets.append({"Type": "GATEWAY", "Resource": visa_res})

    # C. USB
    print(f"   👉 Scanning USB/Local Bus...", end="", flush=True)
    try:
        local_res = rm.list_resources("?*")
        count = 0
        for res in local_res:
            if "TCPIP" not in res and "ASRL" not in res:
                potential_targets.append({"Type": "LOCAL", "Resource": res})
                count += 1
        print(f" Found {count}.")
    except:
        print(" Error.")

    print(f"\n   ⏳ Pausing 2s for settling...")
    time.sleep(2.0)

    # 3. PROBE
    print(f"\n[3/4] PROBING INSTRUMENTS...")
    device_collection = {}

    for idx, target in enumerate(potential_targets):
        raw_res = target["Resource"]
        display_res = clean_string_for_display(raw_res)

        print(f"   🎯 Probing {display_res} ... ", end="", flush=True)

        conn_details = parse_resource_details(display_res)
        idn = query_device_safe(rm, raw_res)

        device_entry = {
            "id": str(idx + 1),
            "type": target["Type"],
            "resource_string": display_res,
            "ip_address": conn_details["IP"],
            "interface_port": conn_details["Interface"],
            "gpib_address": conn_details["GPIB_Addr"],
        }

        if idn:
            print(f"SUCCESS")
            mfg, model, serial, firm = parse_idn(idn)
            device_entry.update(
                {
                    "status": "Active",
                    "manufacturer": mfg,
                    "model": model,
                    "serial_number": serial,
                    "firmware": firm,
                }
            )
            # AUGMENT WITH KNOWLEDGE BASE
            device_entry = augment_device_details(device_entry)
        else:
            print(f"TIMEOUT")
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

        device_collection[str(idx + 1)] = device_entry

    # 4. REPORT
    print(f"\n[4/4] FINAL FLEET INVENTORY")
    print("=" * 140)
    print(
        f"{'ID':<3} | {'MODEL':<8} | {'TYPE':<20} | {'IP ADDRESS':<15} | {'ADDR':<8} | {'NOTES'}"
    )
    print("-" * 140)

    for key, d in device_collection.items():
        model = (d["model"][:8]) if len(d["model"]) > 8 else d["model"]
        dtype = (
            (d["device_type"][:20]) if len(d["device_type"]) > 20 else d["device_type"]
        )

        print(
            f"{key:<3} | {model:<8} | {dtype:<20} | {d['ip_address']:<15} | {d['gpib_address']:<8} | {d['notes']}"
        )
    print("=" * 140)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, OUTPUT_FILENAME)

    try:
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(device_collection, f, indent=4)
        print(f"\n💾 Inventory Saved: {full_path}")
    except Exception as e:
        print(f"   ❌ Error writing JSON: {e}")


if __name__ == "__main__":
    main()
