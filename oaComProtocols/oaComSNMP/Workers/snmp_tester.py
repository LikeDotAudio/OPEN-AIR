# Workers/snmp_tester.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import re
import subprocess

from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Core.logger import get_logger
from oaOchestration.Constants.project_paths import SNMP_TEMP_MIB

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
app_constants = Config.get_instance()
snmp_logger = get_logger("SNMP")

class SnmpTester:
    @staticmethod
    def _debug_enabled():
        return LOCAL_DEBUG or app_constants.SNMP_DEBUG_ENABLE

    @staticmethod
    def verify_oid_tree(base_oid, mib_content=None, mib_path=None):
        """
        Runs snmpwalk locally.
        If no MIB is provided, it returns RAW numerical OIDs (-On).
        If a MIB is provided, it returns translated symbolic names (-Os) with diagnostics.
        """
        temp_mib = str(SNMP_TEMP_MIB)
        active_mib_path = mib_path

        # ⚡ TARGET PLUMPING: If walking the absolute root, append .1 to reach the populated v1 tree
        if base_oid == ".1.3.6.1.4.1.65300":
            base_oid = f"{base_oid}.1"

        # --- RAW MODE: No MIB provided ---
        if not active_mib_path and not mib_content:
            # -Cc: Continue on error (sometimes helpful for walk)
            cmd = ["snmpwalk", "-v2c", "-c", "public", "-On", "localhost", base_oid]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                output = result.stdout
                if result.stderr: output = "ERRORS/WARNINGS:\n" + result.stderr + "\n" + "-"*40 + "\n" + output
                return output if output.strip() else "No OID data returned. Is snmpd running?"
            except Exception as e:
                snmp_logger.error(f"Raw Walk Exception: {e}")
                return f"Raw Walk Exception: {e}"

        # --- MIB MODE: MIB provided or requested ---
        diagnostics = ["SNMP DIAGNOSTIC REPORT", "="*40]

        # 1. Check for system MIBs
        std_mib_path = "/usr/share/snmp/mibs"
        fallback_path = "/usr/share/apps/snmpb/mibs"

        has_std_mibs = os.path.exists(os.path.join(std_mib_path, "SNMPv2-SMI.txt")) or \
                       os.path.exists(os.path.join(std_mib_path, "SNMPv2-SMI"))

        if not has_std_mibs:
            diagnostics.append("! SYSTEM MIBS MISSING: Found no 'SNMPv2-SMI' in /usr/share/snmp/mibs.")
            if os.path.exists(fallback_path):
                diagnostics.append(f"* Using found fallback MIB path: {fallback_path}")
            else:
                diagnostics.append("  Fix: sudo apt-get install snmp-mibs-downloader")
        else:
            diagnostics.append("- System MIBs found in /usr/share/snmp/mibs.")

        # 2. Process custom MIB
        module_name = "OPENAIR-MIB"
        if not active_mib_path and mib_content:
            try:
                with open(temp_mib, "w") as f:
                    f.write(mib_content)
                active_mib_path = temp_mib
            except Exception as e:
                snmp_logger.error(f"FAILED to write temporary MIB: {e}")
                diagnostics.append(f"! FAILED to write temporary MIB: {e}")

        if active_mib_path and os.path.exists(active_mib_path):
            diagnostics.append(f"- Custom MIB found: {os.path.basename(active_mib_path)}")
            # Detect module name
            try:
                with open(active_mib_path) as f:
                    first_lines = f.read(2000)
                    match = re.search(r"^([\w-]+)\s+DEFINITIONS\s+::=\s+BEGIN", first_lines, re.MULTILINE)
                    if match:
                        module_name = match.group(1)
                        diagnostics.append(f"- Module name detected: {module_name}")
            except Exception as e:
                snmp_logger.debug(f"Failed to detect module name from MIB: {e}")
        else:
            diagnostics.append("! No custom MIB provided or found.")

        # Phase 2: Execution
        env = os.environ.copy()

        if active_mib_path:
            mib_dir = os.path.dirname(os.path.abspath(active_mib_path))
            search_paths = [mib_dir]
            if os.path.exists(std_mib_path): search_paths.append(std_mib_path)
            if os.path.exists(fallback_path): search_paths.append(fallback_path)

            search_path_str = ":".join(search_paths)
            env["MIBDIRS"] = f"{search_path_str}" # ⚡ ABSOLUTE search path

            # Build Command
            # -OS: Full symbolic names
            # -m ALL: Load all MIBs in search path
            # -Cc: Continue on error (critical for identity nodes)
            cmd = ["snmpwalk", "-v2c", "-c", "public",
                   "-Cc",
                   "-M", search_path_str,
                   "-m", "ALL",
                   "-OS",
                   "localhost", base_oid]
        else:
            cmd = ["snmpwalk", "-v2c", "-c", "public", "localhost", base_oid]

        diagnostics.append(f"> Executing walk on {base_oid}...")
        diagnostics.append("="*40 + "\n")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, env=env)
            output = result.stdout
            if result.stderr:
                output = "SNMPWALK ERRORS/WARNINGS:\n" + result.stderr + "\n" + "-"*40 + "\n" + output

            if not output.strip() and result.returncode == 0:
                output = "No data returned. Bridge is active but tree is empty."
            elif not output.strip():
                output = "No data returned and walk failed. Check snmpd logs."
        except Exception as e:
            snmp_logger.error(f"Process Exception during SNMP walk: {e}")
            output = f"Process Exception: {e}"

        return "\n".join(diagnostics) + output
