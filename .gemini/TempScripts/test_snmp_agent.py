import sys
import os

# Ensure the project root is in sys.path
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaComSNMP.Methods.snmp_agent import SnmpAgent

def test_snmp_agent():
    agent = SnmpAgent()
    
    # Insert OIDs out of order
    agent.update_oid(".1.3.6.1.4.1.1.1", "Value 1")
    agent.update_oid(".1.3.6.1.4.1.1.3", "Value 3")
    agent.update_oid(".1.3.6.1.4.1.1.2", "Value 2")
    
    # Test GET
    v = agent.get_oid(".1.3.6.1.4.1.1.2")
    print(f"GET .1.3.6.1.4.1.1.2: {v}")
    
    # Test GETNEXT
    next_node = agent.get_next(".1.3.6.1.4.1.1.1")
    print(f"GETNEXT after .1.3.6.1.4.1.1.1: {next_node}")
    
    if v == "Value 2" and next_node and next_node['oid'] == ".1.3.6.1.4.1.1.2":
        print("✅ SUCCESS: SNMP OID tree managed correctly in Rust.")
    else:
        print(f"❌ FAILURE: Data mismatch: {v}, {next_node}")

if __name__ == "__main__":
    test_snmp_agent()
