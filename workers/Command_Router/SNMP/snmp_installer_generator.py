# managers/SNMP/snmp_installer_generator.py
import os

class InstallerGenerator:
    @staticmethod
    def generate(base_oid, master_script_path):
        """
        Generates a complete Bash Installer Script for the SNMP Manager.
        Updated to ensure absolute path synchronization and permission robustness.
        """
        # Ensure we use the absolute path for the bridge script
        abs_master_path = os.path.abspath(master_script_path)
        
        installer_lines = [
            "#!/bin/bash",
            "# OPEN-AIR SNMP Master Bridge: Automated Installer",
            "",
            "# 1. Install Prerequisites",
            "echo \"[SNMP] Installing snmpd and utilities...\"",
            "sudo apt-get update && sudo apt-get install snmpd snmp snmp-mibs-downloader -y",
            "",
            "# 2. Permission Fix (Traverse home to access project)",
            "echo \"[SNMP] Adjusting folder permissions for system access...\"",
            "sudo chmod o+x /home /home/anthony /home/anthony/Documents /home/anthony/Documents/OPEN-AIR",
            "sudo chmod -R o+rwx /home/anthony/Documents/OPEN-AIR/DATA/snmp",
            "",
            "# 3. Master Configuration",
            "CONF_FILE=\"/etc/snmp/snmpd.conf\"",
            "echo \"[SNMP] Configuring Master Bridge at $CONF_FILE...\"",
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
            f"pass {base_oid.lstrip('.')} {abs_master_path}",
            "# --- END OPEN-AIR ---",
            "EOT",
            "",
            "# 4. Service Management",
            "echo \"[SNMP] Restarting service...\"",
            "sudo systemctl restart snmpd",
            "sudo systemctl enable snmpd",
            "",
            "echo \"[SNMP] Setup Complete!\"",
            f"echo \"[SNMP] Testing: snmpwalk -v2c -c public localhost {base_oid}\"",
            "sleep 1",
            f"snmpwalk -v2c -c public localhost {base_oid}",
        ]
        
        return "\n".join(installer_lines)
