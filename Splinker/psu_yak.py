# managers/yak/psu_yak.py


class PsuYak:
    def __init__(self, visa_manager):
        self.visa_manager = visa_manager
        print("PsuYak initialized.")

    def handle_command(self, command_string: str):
        """
        Parses the command string from the GUI and dispatches to the appropriate function.
        Expected format: SCPI command e.g., "VOLT 5.0" or "OUTP ON"
        """
        print(f"Executing PSU command: {command_string}")
        # In a real scenario, this would send the SCPI command via the visa_manager.
        # self.visa_manager.write(command_string)

    def set_voltage(self, voltage: float):
        print(f"Setting voltage to {voltage} V.")
        # self.visa_manager.write(f"VOLT {voltage}")

    def set_current(self, current: float):
        print(f"Setting current limit to {current} A.")
        # self.visa_manager.write(f"CURR {current}")

    def set_output_state(self, state: bool):
        status = "ON" if state else "OFF"
        print(f"Setting output state to {status}.")
        # self.visa_manager.write(f"OUTP {1 if state else 0}")
