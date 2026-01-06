LOCAL_DEBUG_ENABLE = False

# managers/frequency_manager/frequency_state.py


class FrequencyState:
    """Holds the state for frequency-related settings."""

    def __init__(self):
        self.base_topic = "OPEN-AIR/configuration/instrument/frequency"
        self.center_freq = None
        self.span_freq = None
        self.start_freq = None
        self.stop_freq = None
        self.preset_values = {}
        self._locked_state = {
            f"{self.base_topic}/Settings/fields/center_freq_MHz/value": False,
            f"{self.base_topic}/Settings/fields/span_freq_MHz/value": False,
            f"{self.base_topic}/Settings/fields/start_freq_MHz/value": False,
            f"{self.base_topic}/Settings/fields/stop_freq_MHz/value": False,
        }
