# oaDataSNMP/Entry.py
# Author: Gemini (Collaborator)
# Version: 20260324.2200.1
#
# Description: SNMP Data Module Entry Point - Manages OID State and Configurations.

import os
from pathlib import Path
from oaOchestration.Constants.project_paths import (
    SNMP_STATE_FILE,
    SNMP_SET_LOG,
    SNMP_CURRENT_MIB,
    SNMP_DATA_DIR
)

class SnmpDataEntry:
    """
    Public interface for SNMP Data.
    Handles storage paths and state file access for the SNMP subsystem.
    """
    def __init__(self):
        self.state_file = SNMP_STATE_FILE
        self.set_log = SNMP_SET_LOG
        self.mib_file = SNMP_CURRENT_MIB
        self.data_dir = SNMP_DATA_DIR
        self.pass_scripts_dir = self.data_dir / "pass_scripts"
        
        # Ensure directories exist
        self.pass_scripts_dir.mkdir(parents=True, exist_ok=True)

    def get_state_path(self):
        return str(self.state_file)

    def get_log_path(self):
        return str(self.set_log)

    def get_mib_path(self):
        return str(self.mib_file)

    def get_master_script_path(self):
        return str(self.pass_scripts_dir / "master_snmp_bridge.sh")

__all__ = [
    "SnmpDataEntry",
]
