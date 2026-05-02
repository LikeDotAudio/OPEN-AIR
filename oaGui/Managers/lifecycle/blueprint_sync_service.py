# oaGui/Managers/lifecycle/blueprint_sync_service.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for loading blueprints and synchronizing background state.

from oaGui.FileReaders.loader.json_blueprint_reader import JsonBlueprintReader

def load_and_synchronize_blueprint(loader_instance):
    """Loads JSON blueprint, verifies hashes, and applies background configurations."""
    configuration, new_hash, is_changed = JsonBlueprintReader.load_blueprint(
        loader_instance.json_filepath,
        loader_instance.tab_name,
        loader_instance.last_build_hash
    )

    if not is_changed and loader_instance.json_filepath:
        return

    if configuration is None:
        if loader_instance.json_filepath: return
        configuration = {}

    loader_instance.configuration = configuration
    if new_hash: loader_instance.last_build_hash = new_hash

    # Apply Background
    bg_config = configuration.get("background")
    if bg_config and bg_config != "none":
        if hasattr(loader_instance, '_apply_panel_background'):
            loader_instance._apply_panel_background(bg_config)

    # Broadcast initial state
    if hasattr(loader_instance, '_publish_json_to_topic'):
        loader_instance._publish_json_to_topic(configuration)
    if hasattr(loader_instance, '_publish_initial_widget_states'):
        loader_instance._publish_initial_widget_states(configuration)

    loader_instance._rebuild_gui()
    loader_instance.gui_built = True
