# managers/SNMP/snmp_installer_generator.py
import os

class InstallerGenerator:
    @staticmethod
    def generate(base_oid, master_script_path):
        """
        Generates a complete Bash Installer Script for the SNMP Manager.
        Updated to ensure path references are relative to the project root.
        """
        # Construct the relative path for the master script.
        # We assume master_script_path is provided relative to the project root.
        # Ensure it's prefixed with './' if it doesn't start with '.' or '/'.
        relative_master_path = master_script_path
        if not relative_master_path.startswith('.') and not relative_master_path.startswith('/'):
             relative_master_path = './' + relative_master_path
        
        installer_lines = [
            "#!/bin/bash",
            "# OPEN-AIR SNMP Master Bridge: Automated Installer",
            "",
            "# 1. Install Prerequisites",
            "echo "[SNMP] Installing snmpd and utilities..."",
            "sudo apt-get update && sudo apt-get install snmpd snmp snmp-mibs-downloader -y",
            "",
            "# 2. Permission Fix (Traverse home to access project)",
            "echo "[SNMP] Adjusting folder permissions for system access..."",
            "sudo chmod o+x /home /home/anthony",
            "sudo chmod -R o+rwx ./oaDataRunningFiles/snmp",

            "# 3. Master Configuration",
            "CONF_FILE="/etc/snmp/snmpd.conf"",
            "echo "[SNMP] Configuring Master Bridge at $CONF_FILE..."",
            "",
            "# Clean up old configurations",
            "sudo sed -i '/# --- BEGIN OPEN-AIR ---/,/# --- END OPEN-AIR ---/d' $CONF_FILE",
            "sudo sed -i '/pass .1.3.6.1.4.1.25030/d' $CONF_FILE",
            "sudo sed -i '/pass 1.3.6.1.4.1.25030/d' $CONF_FILE",
            "",
            "# Inject Fresh Master Bridge",
            "sudo tee -a $CONF_FILE > /dev/null <<EOT",
            "# --- BEGIN OPEN-AIR ---",
            "agentAddress udp:161",
            "view   all   included   .1",
            "rocommunity public default -V all",
            "rwcommunity private default -V all",
            f"pass {base_oid.lstrip('.')} {relative_master_path}", # Use constructed relative path
            "# --- END OPEN-AIR ---",
            "EOT",
            "",
            "# 4. Service Management",
            "echo "[SNMP] Restarting service..."",
            "sudo systemctl restart snmpd",
            "sudo systemctl enable snmpd",
            "",
            "echo "[SNMP] Setup Complete!"",
            f"echo "[SNMP] Testing: snmpwalk -v2c -c public localhost {base_oid}"",
            "sleep 1",
            f"snmpwalk -v2c -c public localhost {base_oid}",
        ]
        
        return "
".join(installer_lines)
