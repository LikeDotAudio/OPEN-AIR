# managers/SNMP/snmp_mib_generator.py
import datetime
import zlib
from loguru import logger
from oaConfiguration.config_reader import Config
from oaComSNMP.snmp_utils import get_snmp_node_id, get_snmp_descriptor

# --- Standard Debug Logging Setup ---
snmp_mib_generator_verbose_logging_enabled = False
app_constants = Config.get_instance()
snmp_logger = logger.bind(subsystem="SNMP")

class MibGenerator:
    @staticmethod
    def generate(base_oid, oid_map, organization="OPEN-AIR Project"):
        """
        Generates a SMIv2 MIB file with unique descriptors.
        Uses OPENAIR-MIB consistently.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
        pen = base_oid.split('.')[-1]
        
        if snmp_mib_generator_verbose_logging_enabled:
            snmp_logger.debug(f"📜 SNMP MIB: Starting generation for {len(oid_map)} OIDs...")

        lines = [
            f"OPENAIR-MIB DEFINITIONS ::= BEGIN",
            "",
            f"IMPORTS",
            f"    MODULE-IDENTITY, OBJECT-TYPE, enterprises FROM SNMPv2-SMI",
            f"    DisplayString FROM SNMPv2-TC;",
            "",
            f"openAirMIB MODULE-IDENTITY",
            f"    LAST-UPDATED \"{timestamp}Z\"",
            f"    ORGANIZATION \"{organization}\"",
            f"    CONTACT-INFO \"Anthony Peter Kuzub\"",
            f"    DESCRIPTION \"MQTT-Aligned OID Tree for OPEN-AIR.\"",
            f"    REVISION \"{timestamp}Z\"",
            f"    DESCRIPTION \"Strictly unique path-aligned generation.\"",
            f"    ::= {{ enterprises {pen} }}",
            "",
            f"v1 OBJECT IDENTIFIER ::= {{ openAirMIB 1 }}",
            ""
        ]

        # Build hierarchy tree
        tree = {}
        for oid, data in sorted(oid_map.items()):
            parts = data.get("path_parts", [])
            if not parts: continue
            
            curr_level = tree
            curr_parent_desc = "v1"
            path_acc_parts = []
            
            for i, part in enumerate(parts):
                path_acc_parts.append(part)
                node_id = get_snmp_node_id(path_acc_parts)
                final_descriptor = get_snmp_descriptor(path_acc_parts)
                
                if part not in curr_level:
                    curr_level[part] = {
                        "node_id": node_id,
                        "children": {},
                        "descriptor": final_descriptor,
                        "parent_descriptor": curr_parent_desc,
                        "topic": None
                    }
                
                # Update topic if it's a leaf
                if i == len(parts) - 1:
                    curr_level[part]["topic"] = data["topic"]
                
                curr_parent_desc = final_descriptor
                curr_level = curr_level[part]["children"]

        def write_nodes(level_dict):
            # Sort items by node_id numerically for a clean walk
            sorted_items = sorted(level_dict.items(), key=lambda x: int(x[1]["node_id"]))
            
            for part, node_data in sorted_items:
                desc = node_data["descriptor"]
                parent = node_data["parent_descriptor"]
                nid = node_data["node_id"]
                
                if node_data["children"]:
                    lines.append(f"{desc} OBJECT IDENTIFIER ::= {{ {parent} {nid} }}")
                    write_nodes(node_data["children"])
                elif node_data["topic"]:
                    lines.append(f"-- MQTT: {node_data['topic']}")
                    lines.append(f"{desc} OBJECT-TYPE")
                    lines.append(f"    SYNTAX      DisplayString")
                    lines.append(f"    MAX-ACCESS  read-write")
                    lines.append(f"    STATUS      current")
                    lines.append(f"    DESCRIPTION \"Source: {node_data['topic']}\"")
                    lines.append(f"    ::= {{ {parent} {nid} }}")
                    lines.append("")

        write_nodes(tree)
        lines.append("END")
        return "\n".join(lines)
