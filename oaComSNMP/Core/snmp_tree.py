# oaComSNMP/Core/snmp_tree.py
#
# Master tree builder for the OPEN-AIR SNMP OID structure.
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
# Version 20260329.1025.1

import os
import stat
from oaLogging.Core.logger import get_logger
from oaConfiguration.FileReaders.config_reader import Config
from oaOchestration.Constants.project_paths import SNMP_STATE_FILE, SNMP_SET_LOG
from oaComSNMP.Constants.snmp_constants import BASE_OID

# --- Standard Debug Logging Setup ---
snmp_tree_builder_verbose_logging_enabled = False
app_constants = Config.get_instance()
snmp_logger = get_logger("SNMP")

class SNMPTreeBuilder:
    def __init__(self, base_oid=BASE_OID):
        self.base_oid = base_oid
        from oaOchestration.Constants.project_paths import SNMP_DATA_DIR
        self.script_dir = SNMP_DATA_DIR / "pass_scripts"
        os.makedirs(self.script_dir, exist_ok=True)
        self.master_script_path = self.script_dir / "master_snmp_bridge.sh"

    def _verbose_logging_enabled(self):
        return snmp_tree_builder_verbose_logging_enabled

    def generate_master_script(self):
        """Generates a single master script to handle the entire OPEN-AIR OID tree."""
        if self._verbose_logging_enabled(): snmp_logger.debug(f"📜 SNMP: Generating Master Bridge script at {self.master_script_path}...")
        
        # ⚡ SYSTEM ACCESS: Use absolute paths for snmpd visibility
        flat_file = os.path.abspath(str(SNMP_STATE_FILE))
        log_file = os.path.abspath(str(SNMP_SET_LOG))
        debug_log = os.path.join(os.path.dirname(flat_file), "bridge_debug.log")
        
        lines = [
            "#!/bin/bash",
            "# OPEN-AIR Master SNMP Bridge",
            f"FLAT_FILE=\"{flat_file}\"",
            f"LOG_FILE=\"{log_file}\"",
            f"DEBUG_LOG=\"{debug_log}\"",
            "",
            "# Log all requests for debugging",
            "echo \"[$(date)] REQ: $1 $2\" >> $DEBUG_LOG",
            "",
            "# Handle SET (-s)",
            "if [ \"$1\" = \"-s\" ]; then",
            "    echo \"-s $2 $3 $4\" >> $LOG_FILE",
            "    exit 0",
            "fi",
            "",
            # Unified GET/GETNEXT Handler using AWK
            "awk -F':' -v cmd=\"$1\" -v target=\"$2\" '",
            "    function norm(oid) {",
            "        gsub(/^[.\"]+|[.\"]+$/, \"\", oid);",
            "        split(oid, p, \".\");",
            "        out = \"\";",
            "        for (i=1; i<=length(p); i++) {",
            "            out = out sprintf(\"%010d.\", p[i]);",
            "        }",
            "        return out;",
            "    }",
            "    BEGIN { ",
            "        t = norm(target); ",
            "        found = 0; ",
            "    }",
            "    {",
            "        c = norm($1);",
            "        if (cmd == \"-g\") {",
            "            if (c == t) {",
            "                # Print OID without leading dot",
            "                print ($1 ~ /^\\./ ? substr($1, 2) : $1);",
            "                print \"string\";",
            "                print substr($0, index($0, \":\") + 1);",
            "                found = 1;",
            "                exit 0;",
            "            }",
            "        } else if (cmd == \"-n\") {",
            "            if (c > t) {",
            "                # Print OID without leading dot",
            "                print ($1 ~ /^\\./ ? substr($1, 2) : $1);",
            "                print \"string\";",
            "                print substr($0, index($0, \":\") + 1);",
            "                found = 1;",
            "                exit 0;",
            "            }",
            "        }",
            "    }",
            "    END { if (!found) exit 1; }",
            "    ' \"$FLAT_FILE\"",
            "",
            "if [ $? -ne 0 ]; then",
            "    echo \"[$(date)] NOT FOUND: $2\" >> $DEBUG_LOG",
            "fi"
        ]

        try:
            with open(self.master_script_path, "w") as f:
                f.write("\n".join(lines) + "\n")
            # 🔐 SYSTEM ACCESS: Ensure script is executable by all users (snmp user)
            os.chmod(self.master_script_path, 0o755)
            return self.master_script_path
        except Exception as e:
            snmp_logger.error(f"❌ Failed to generate master script: {e}")
            return None

    def generate_pass_script(self, device_id, device_type, oca_objects):
        """Legacy method kept for compatibility, but we now use the Master Script."""
        return self.generate_master_script()
