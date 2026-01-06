# managers/yak/signal_generator_yak.py


class SignalGeneratorYak:
    def __init__(self, visa_manager):
        self.visa_manager = visa_manager
        print("SignalGeneratorYak initialized.")

    def handle_command(self, command_string: str):
        """
        Parses the command string from the GUI and dispatches to the appropriate function.
        Expected format: SCPI command e.g., "FREQ 1e6"
        """
        print(f"Executing signal generator command: {command_string}")
        # In a real scenario, this would send the SCPI command via the visa_manager.
        # self.visa_manager.write(command_string)

    def set_frequency(self, frequency: float):
        print(f"Setting frequency to {frequency} Hz.")
        # self.visa_manager.write(f"FREQ {frequency}")

    def set_amplitude(self, amplitude: float):
        print(f"Setting amplitude to {amplitude} dBm.")
        # self.visa_manager.write(f"POWER {amplitude}")

    def set_output_state(self, state: bool):
        status = "ON" if state else "OFF"
        print(f"Setting output state to {status}.")
        # self.visa_manager.write(f"OUTPUT:STATE {1 if state else 0}")
