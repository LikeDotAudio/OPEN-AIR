import serial
import serial.tools.list_ports
import time
import sys


def select_serial_port():
    """
    Scans for available serial ports and asks the user to select one.
    Returns the selected port device name (e.g., '/dev/ttyUSB0' or 'COM3').
    """
    ports = list(serial.tools.list_ports.comports())

    if not ports:
        print("\n[!] No serial devices found.")
        print("    Check your cable connection and drivers.")
        sys.exit(1)

    print("\n--- Available Serial Devices ---")
    for index, port in enumerate(ports):
        # port.device = the system path (e.g., COM3, /dev/ttyUSB0)
        # port.description = human readable name (e.g., FTDI Serial)
        print(f"{index + 1}: {port.device} - {port.description}")

    while True:
        try:
            selection = input("\nSelect a device number: ")
            idx = int(selection) - 1
            if 0 <= idx < len(ports):
                selected_port = ports[idx].device
                print(f"[*] You selected: {selected_port}")
                return selected_port
            else:
                print(f"[!] Invalid number. Please enter 1-{len(ports)}.")
        except ValueError:
            print("[!] Please enter a valid integer.")


def main():
    # 1. Get the port from the user
    port_name = select_serial_port()

    # 2. Configure the connection for Fluke 43B
    # Note: Fluke optical cables are notoriously slow.
    # If 1200 baud fails, try 9600 or 19200.
    BAUD_RATE = 1200

    print(f"\n[*] Attempting to connect to {port_name} at {BAUD_RATE} baud...")

    try:
        ser = serial.Serial(
            port=port_name,
            baudrate=BAUD_RATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2,  # Longer timeout for older hardware
        )

        # 3. Send a "Wake Up" / ID Command
        # The Fluke 43B protocol is binary. Sending 0x01 or 0x0F is a common
        # way to trigger a response (Identity request).
        # Note: Without a specific command, the device sits silently.
        command_byte = b"\x01"

        print(f"[*] Sending query byte: {command_byte.hex()}")
        ser.write(command_byte)

        # 4. Wait for response
        time.sleep(1.0)

        if ser.in_waiting > 0:
            raw_data = ser.read(ser.in_waiting)
            print(f"\n[SUCCESS] Received {len(raw_data)} bytes:")
            print(f"    Raw Hex: {raw_data.hex()}")
            print(f"    ASCII:   {raw_data}")
        else:
            print("\n[?] No data received.")
            print("    Troubleshooting:")
            print("    1. Is the Fluke 43B turned ON?")
            print("    2. Is the optical eye aligned correctly?")
            print("    3. Try changing baudrate to 9600 or 19200.")

        ser.close()

    except serial.SerialException as e:
        print(f"\n[ERROR] Could not open port {port_name}.")
        print(f"Reason: {e}")
    except KeyboardInterrupt:
        print("\n[*] Exiting...")


if __name__ == "__main__":
    main()
