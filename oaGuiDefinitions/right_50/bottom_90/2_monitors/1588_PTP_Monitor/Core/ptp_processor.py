# Core/ptp_processor.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import datetime

class PTPDataProcessor:
    """Handles timestamp analysis, data ordering, and categorization for PTP packets."""

    @staticmethod
    def process_packet(data):
        ts_raw = data["timestamp"]
        dt = datetime.datetime.fromtimestamp(ts_raw)
        
        seconds = int(ts_raw)
        fraction = ts_raw - seconds
        ms = int(fraction * 1000)
        us = int((fraction * 1_000_000) % 1000)
        ns = int((fraction * 1_000_000_000) % 1000)

        breakdown = {
            "0_Raw_Unix_Float": f"{ts_raw:.9f}",
            "1_Epoch_Seconds": f"{seconds} (Seconds since Jan 1, 1970)",
            "2_Sub_Second_Remainder": f"{fraction:.9f}",
            "3_Calendar_Breakdown": {
                "Year": dt.year, "Month": f"{dt.month} ({dt.strftime('%B')})",
                "Day": dt.day, "Hour": dt.hour, "Minute": dt.minute,
                "Second": dt.second, "ISO_8601": dt.isoformat()
            },
            "4_Resolution_Breakdown": {
                "Milliseconds": f"{ms} ms", "Microseconds": f"{us} \u00b5s", "Nanoseconds": f"{ns} ns"
            }
        }
        
        ordered = {"Timestamp_Analysis": breakdown}
        ordered.update(data)
        
        msg_type = data["message_type"]
        tag = "Sync" if "Sync" in msg_type else ("Announce" if "Announce" in msg_type else ("Follow_Up" if "Follow_Up" in msg_type else ""))
        
        return ordered, dt.strftime('%H:%M:%S.%f')[:-3], tag
