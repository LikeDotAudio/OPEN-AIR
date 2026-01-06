# managers/bandwidth_manager/bandwidth_state.py
#
# This file is part of the OPEN-AIR project.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
#
# Version 20251213.120000.44

# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# As the current hour is 20, no change is needed.

Current_Date = 20251213
Current_Time = 120000
Current_iteration = 44

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = Current_Date * Current_Time * Current_iteration

LOCAL_DEBUG_ENABLE = False


class BandwidthState:
    """Holds the state for bandwidth-related settings."""

    def __init__(self):
        self.base_topic = "OPEN-AIR/configuration/instrument/bandwidth"

        self.rbw_value = None
        self.vbw_value = None
        self.sweep_time_value = None

        self.rbw_preset_values = {}
        self.vbw_preset_values = {}

        self.rbw_preset_units = {}
        self.vbw_preset_units = {}

        self._locked_state = {
            f"{self.base_topic}/Settings/fields/Resolution Bandwidth/fields/RBW/value": False,
            f"{self.base_topic}/Settings/fields/Sweep_time_s/value": False,
            f"{self.base_topic}/Settings/fields/Video Bandwidth/fields/vbw_MHz/value": False,
            f"{self.base_topic}/Settings/fields/Video Bandwidth/fields/VBW_Automatic/options/ON/selected": False,
            f"{self.base_topic}/Settings/fields/Video Bandwidth/fields/VBW_Automatic/options/OFF/selected": False,
            f"{self.base_topic}/Settings/fields/Sweep_Mode/options/Continuous/selected": False,
            f"{self.base_topic}/Settings/fields/Sweep_Mode/options/Single/selected": False,
        }

    UNIT_MULTIPLIERS = {
        "HZ": 1,
        "KHZ": 1000,
        "MHZ": 1000000,
        "GHZ": 1000000000,
        "S": 1,
        "MS": 0.001,
        "US": 0.000001,
    }

    def get_multiplier(self, unit_string: str) -> float:
        clean_unit = unit_string.strip().upper()
        return self.UNIT_MULTIPLIERS.get(clean_unit, 1.0)
