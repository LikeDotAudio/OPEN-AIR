# oaGui/FileReaders/loader/instance_factory.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for instantiating GUI components from resolved paths.

import inspect
from oaLogging.Entry import vocal_capture
from oaLogging.Methods.matrix_gate import matrix_log
from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import generate_topic_path_from_filepath
from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
from oaGui.FileReaders.loader.json_gui_host import JsonGuiHost

def create_gui_instance(loader_instance, python_path, json_path, parent_widget):
    """Orchestrates the physical instantiation of a Python or JSON based GUI."""
    if python_path:
        target_class = loader_instance.load_module_from_path(python_path)
        if target_class:
            return loader_instance.instantiate_widget(target_class, parent_widget, python_path)
        return None

    if json_path:
        try:
            config = {
                "theme_colors": loader_instance.theme_colors,
                "state_mirror_engine": loader_instance.state_mirror_engine,
                "subscriber_router": loader_instance.subscriber_router,
                "app_instance": loader_instance.app_instance,
                "json_path": str(json_path),
            }
            config["base_mqtt_topic_from_path"] = generate_topic_path_from_filepath(json_path, GLOBAL_PROJECT_ROOT)

            instance = JsonGuiHost(parent=parent_widget, json_path=str(json_path), config=config)
            loader_instance.instantiator.builders.append(instance)
            
            matrix_log("UI", "loader", "instantiate", f"🏗️🪟✨ Created {json_path}!", level="SUCCESS")
            return instance
        except Exception:
            vocal_capture("UI", f"Error instantiating JsonGuiHost for '{json_path}'")
            return None

    return None
