# oaComProtocols.oaComSNMP/Methods/snmp_installer_generator.py
#
# Generates a complete Bash Installer Script for the SNMP Manager.
#
# Author: Anthony Peter Kuzub (Contributor to this project)
# Blog: www.Like.audio
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260329.1030.1

import os

class InstallerGenerator:
    @staticmethod
    def generate(base_oid, master_script_path):
        """
        Generates a complete Bash Installer Script for the SNMP Manager.
        Ensures path references are absolute and robust for snmpd access.
        """
        from oaConfigurationManager.FileReaders.config_reader import Config
        from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
        from oaOchestration.Constants.project_paths import DATA_SNMP_DIR
        configuration = Config.get_instance()

        # We must use absolute paths for the snmpd.conf 'pass' command 
        # because snmpd runs as a system service and won't know the project root.
        abs_master_path = os.path.abspath(master_script_path)
        abs_data_dir = os.path.abspath(DATA_SNMP_DIR)
        
        installer_lines = [
            "#!/bin/bash",
            "# OPEN-AIR SNMP Master Bridge: Automated Installer",
            "",
            "# 1. Install Prerequisites",
            'echo "[SNMP] Installing snmpd and utilities..."',
            "sudo apt-get update && sudo apt-get install snmpd snmp snmp-mibs-downloader -y",
            "",
            "# 2. Permission Fix (Traverse home to access project)",
            'echo "[SNMP] Adjusting folder permissions for system access..."',
            "sudo chmod o+x /home /home/anthony",
            f"sudo chmod -R o+rwx {abs_data_dir}",

            "# 3. Master Configuration",
            "CONF_FILE='/etc/snmp/snmpd.conf'",
            'echo "[SNMP] Configuring Master Bridge at $CONF_FILE..."',
            "",
            "# Clean up old configurations",
            "sudo sed -i '/# --- BEGIN OPEN-AIR ---/,/# --- END OPEN-AIR ---/d' $CONF_FILE",
            "sudo sed -i '/pass .1.3.6.1.4.1.65300/d' $CONF_FILE",
            "sudo sed -i '/pass 1.3.6.1.4.1.65300/d' $CONF_FILE",
            "",
            "# Inject Fresh Master Bridge",
            "sudo tee -a $CONF_FILE > /dev/null <<EOT",
            "# --- BEGIN OPEN-AIR ---",
            f"agentAddress udp:{configuration.SNMP_PORT}",
            "view   all   included   .1",
            "rocommunity public default -V all",
            "rwcommunity private default -V all",
            f"pass {base_oid.lstrip('.')} {abs_master_path}",
            "# --- END OPEN-AIR ---",
            "EOT",
            "",
            "# 4. Service Management",
            'echo "[SNMP] Restarting service..."',
            "sudo systemctl restart snmpd",
            "sudo systemctl enable snmpd",
            "",
            'echo "[SNMP] Setup Complete!"',
        ]
        
        return '\n'.join(installer_lines)
