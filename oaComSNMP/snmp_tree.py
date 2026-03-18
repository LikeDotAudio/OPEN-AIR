# workers/Command_Router/SNMP/snmp_tree.py
import os
import stat
from loguru import logger
from oaConfiguration.config_reader import Config
from oaOchestration.project_paths import SNMP_STATE_FILE, SNMP_SET_LOG

# --- Standard Debug Logging Setup ---
snmp_tree_builder_verbose_logging_enabled = False
app_constants = Config.get_instance()
snmp_logger = logger.bind(subsystem="SNMP")

class SNMPTreeBuilder:
    def __init__(self, base_oid=".1.3.6.1.4.1.25030"):
        self.base_oid = base_oid
        from oaOchestration.project_paths import SNMP_DATA_DIR
        self.script_dir = SNMP_DATA_DIR / "pass_scripts"
        os.makedirs(self.script_dir, exist_ok=True)
        self.master_script_path = self.script_dir / "master_snmp_bridge.sh"

    def _verbose_logging_enabled(self):
        return snmp_tree_builder_verbose_logging_enabled

    def generate_master_script(self):
        """Generates a single master script to handle the entire OPEN-AIR OID tree."""
        if self._verbose_logging_enabled(): snmp_logger.debug(f"📜 SNMP: Generating Master Bridge script at {self.master_script_path}...")
        flat_file = str(SNMP_STATE_FILE)
        log_file = str(SNMP_SET_LOG)
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
