import tkinter as tk
from tkinter import ttk
import pathlib
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from oaGuiBuilder.Workers.builder import DynamicGuiBuilder
from oaTranslator.Core.state_mirror_engine import StateMirrorEngine
from oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter

def main():
    root = tk.Tk()
    root.withdraw()
    
    # Mock dependencies
    sub_router = MqttSubscriberRouter(None)
    mirror_engine = StateMirrorEngine("test", sub_router, root, None)
    
    json_path = "oaGuiDefinitions/right_50/bottom_90/9_Zoo/7_Data/2_demo/demo.json"
    
    print(f"Attempting to build: {json_path}")
    
    try:
        builder = DynamicGuiBuilder(
            parent=root,
            json_path=json_path,
            tab_name="DEMO",
            config={
                "state_mirror_engine": mirror_engine,
                "subscriber_router": sub_router,
                "base_mqtt_topic_from_path": "OPEN-AIR/Zoo/Data/demo"
            }
        )
        print("Builder initialized. Starting build...")
        # The build is triggered in __init__ via _load_and_build_from_file
        
        root.update()
        print("Build complete (initial update).")
        
    except Exception as e:
        print(f"CAUGHT ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("Reproduction script finished.")

if __name__ == "__main__":
    main()
