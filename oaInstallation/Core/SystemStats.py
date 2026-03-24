# Core/SystemStats.py
# Author: Anthony Peter Kuzub
# Version: 20260323.1945.1
#
# Description: Gathers system performance metrics for the installation interface.

import psutil
import shutil
import os

class SystemStatsProvider:
    """
    Provides real-time system resource metrics.
    """
    @staticmethod
    def get_cpu_speed():
        """Returns current CPU frequency in MHz."""
        freq = psutil.cpu_freq()
        if freq:
            return freq.current
        return 0.0

    @staticmethod
    def get_cpu_cores():
        """Returns the number of logical CPU cores."""
        return os.cpu_count()

    @staticmethod
    def get_ram_usage():
        """Returns RAM usage as a percentage and used/total in GB."""
        ram = psutil.virtual_memory()
        used_gb = ram.used / (1024 ** 3)
        total_gb = ram.total / (1024 ** 3)
        return ram.percent, used_gb, total_gb

    @staticmethod
    def get_disk_space(path="/"):
        """Returns disk usage for the specified path."""
        usage = shutil.disk_usage(path)
        percent = (usage.used / usage.total) * 100
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        return percent, free_gb, total_gb

    def get_all_stats(self):
        """Aggregates all system metrics into a dictionary."""
        cpu = self.get_cpu_speed()
        cores = self.get_cpu_cores()
        ram_p, ram_u, ram_t = self.get_ram_usage()
        disk_p, disk_f, disk_t = self.get_disk_space()
        
        return {
            "cpu_mhz": cpu,
            "cpu_cores": cores,
            "ram_percent": ram_p,
            "ram_used_gb": ram_u,
            "ram_total_gb": ram_t,
            "disk_percent": disk_p,
            "disk_free_gb": disk_f,
            "disk_total_gb": disk_t
        }
