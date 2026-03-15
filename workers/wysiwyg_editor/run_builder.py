# workers/wysiwyg_editor/run_builder.py
#
# Standalone entry point for the Modular WYSIWYG Definition Builder.
# Runs as its own process to isolate heavy rendering and avoid UI lag.
#
# Author: Gemini CLI

import sys
import pathlib
import orjson
import tkinter as tk

# 1. Setup Environment: Ensure the project root is in sys.path
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from workers.wysiwyg_editor.wysiwyg_editor import WysiwygEditor
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from workers.styling.theme_applier import apply_theme
from workers.initialization.path_initializer import initialize_paths

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file

def main():
    """Main entry point for the standalone editor program."""
    # ⚡ MANDATORY: Initialize paths so Config reader can find config.ini
    initialize_paths()

    if len(sys.argv) < 2:
        print("Usage: python run_builder.py <json_file_path>")
        sys.exit(1)

    json_filepath = pathlib.Path(sys.argv[1])
    
    # Initialize Root Window
    root = tk.Tk()
    root.title(f"OPEN-AIR: WYSIWYG Editor - {json_filepath.name}")
    
    # ⚡ APPLY THEME: Crucial for visual consistency in standalone process
    if LOCAL_DEBUG: logger.debug("🚀 Standalone Builder: Applying system theme...")
    apply_theme(root)

    if LOCAL_DEBUG: logger.info(f"🚀 Standalone Builder: Starting for {json_filepath}")

    if not json_filepath.exists():
        logger.error(f"❌ Standalone Builder: File not found: {json_filepath}")
        sys.exit(1)

    # Load Initial Data
    try:
        with open(json_filepath, 'rb') as f:
            config_data = orjson.loads(f.read())
    except Exception as e:
        logger.exception("❌ Standalone Builder: Failed to read JSON")
        sys.exit(1)

    def on_test(new_data):
        """Publishes the new config to MQTT to trigger a live rebuild in the main application."""
        if LOCAL_DEBUG: logger.info(f"🏗️ Standalone Builder: 'Test' triggered for {json_filepath.name}")
        
        try:
            # 🛡️ LOCAL IMPORT: Avoid dependency requirement if not testing
            import paho.mqtt.client as mqtt
            from managers.configini.config_reader import Config
            
            app_config = Config.get_instance()
            broker = getattr(app_config, "MQTT_BROKER_ADDRESS", "localhost")
            port = getattr(app_config, "MQTT_BROKER_PORT", 1883)
            user = getattr(app_config, "MQTT_USERNAME", None)
            pw = getattr(app_config, "MQTT_PASSWORD", None)
            
            # ⚡ VERSION 2 API: Suppress deprecation warnings
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            if user and pw:
                client.username_pw_set(user, pw)
            
            # Use short timeout for testing
            client.connect(broker, port, 10)
            
            rebuild_topic = "OPEN-AIR/System/Control/UI/Rebuild"
            payload = {
                "path": str(json_filepath.resolve()),
                "config": new_data
            }
            
            client.publish(rebuild_topic, orjson.dumps(payload))
            client.disconnect()
            
            if LOCAL_DEBUG: logger.success("📡 Standalone Builder: Rebuild request published to MQTT.")
        except ImportError:
            logger.error("❌ Standalone Builder: 'paho-mqtt' library not found. Cannot push to main UI.")
        except Exception as e:
            logger.error(f"❌ Standalone Builder: Failed to publish rebuild request: {e}")

    def on_save():
        if LOCAL_DEBUG: logger.info("🏗️ Standalone Builder: 'Save' operation completed.")
        pass

    # Launch the builder using 'root' as the primary window
    app = WysiwygEditor(
        parent_window=root,
        config_data=config_data,
        json_filepath=json_filepath,
        on_test_callback=on_test,
        on_save_callback=on_save,
        is_standalone=True
    )

    # Lifecycle Management
    def on_close():
        if LOCAL_DEBUG: logger.info("🏗️ Standalone Builder: Program exiting.")
        try:
            app._close_editor()
            root.quit()
            root.destroy()
        except tk.TclError:
            pass
        except Exception as e:
            logger.warning(f"⚠️ Standalone Builder: Error during shutdown: {e}")

    root.protocol("WM_DELETE_WINDOW", on_close)

    # Start Event Loop
    root.mainloop()

if __name__ == "__main__":
    main()
