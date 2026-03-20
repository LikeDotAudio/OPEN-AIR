# oaComVisa/Workers/cli_visa_find.py
# Thin CLI wrapper for the modular VISA discovery system.

import os
from ..Managers.discovery_orchestrator import DiscoveryOrchestrator

def main():
    print(f"--- VISA FLEET MANAGER (MODULAR REFACTOR) ---")
    
    orchestrator = DiscoveryOrchestrator()
    
    # 1-3. Run the full discovery lifecycle
    orchestrator.run_discovery()
    
    # 4. Report and Save
    orchestrator.print_report()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    saved_path = orchestrator.save_inventory(dir_path=script_dir)
    
    if saved_path:
        print(f"\n💾 Inventory Saved: {saved_path}")

if __name__ == "__main__":
    main()
