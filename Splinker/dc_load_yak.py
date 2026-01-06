# managers/yak/dc_load_yak.py


class DcLoadYak:
    def __init__(self, visa_manager):
        self.visa_manager = visa_manager
        print("DcLoadYak initialized.")

    def handle_command(self, command_string: str):
        """
        Parses the command string from the GUI and dispatches to the appropriate function.
        Expected format: SCPI command e.g., "MODE CC" or "CURR 1.0" or "INPUT ON"
        """
        print(f"Executing DC Load command: {command_string}")
        # In a real scenario, this would send the SCPI command via the visa_manager.
        # self.visa_manager.write(command_string)

    def set_mode(self, mode: str):
        print(f"Setting mode to {mode}.")
        # self.visa_manager.write(f"MODE {mode}")

    def set_value(self, mode: str, value: float):
        """Sets the value based on the current mode (e.g., current, voltage, resistance)."""
        print(f"Setting {mode} value to {value}.")
        # command_prefix = {
        #     "CC": "CURR",
        #     "CV": "VOLT",
        #     "CR": "RES",
        #     "CP": "POWER"
        # }.get(mode, "CURR") # Default to Current if mode not found
        # self.visa_manager.write(f"{command_prefix} {value}")

    def set_input_state(self, state: bool):
        status = "ON" if state else "OFF"
        print(f"Setting input state to {status}.")
        # self.visa_manager.write(f"INPUT {1 if state else 0}")
