import os
import re

# Comprehensive mapping for all realignment changes across all folders
mapping = {
    # Managers
    "oaGui.Managers.layout.builder_layout_manager": "oaGui.Managers.layout.builder_layout_manager",
    "oaGui.Managers.persistence.cache_blueprint_store": "oaGui.Managers.persistence.cache_blueprint_store",
    "oaGui.Managers.persistence.cache_layout_store": "oaGui.Managers.persistence.cache_layout_store",
    "oaGui.Managers.grid.engine_grid_layout_logic": "oaGui.Managers.grid.engine_grid_layout_logic",
    "oaGui.Managers.display.engine_gui_display": "oaGui.Managers.display.engine_gui_display",
    "oaGui.Managers.refresh.engine_refresh_coordinator": "oaGui.Managers.refresh.engine_refresh_coordinator",
    "oaGui.Managers.assembler.engine_widget_assembler": "oaGui.Managers.assembler.engine_widget_assembler",
    "oaGui.Managers.assembler.engine_widget_instantiator": "oaGui.Managers.assembler.engine_widget_instantiator",
    "oaGui.Managers.interaction.interaction_navigation": "oaGui.Managers.interaction.interaction_navigation",
    "oaGui.Managers.interaction.interaction_view_states": "oaGui.Managers.interaction.interaction_view_states",
    "oaGui.Managers.bootstrap.loader_bootstrap_engine": "oaGui.Managers.bootstrap.loader_bootstrap_engine",
    "oaGui.Managers.lifecycle.loader_lifecycle_service": "oaGui.Managers.lifecycle.loader_lifecycle_service",
    "oaGui.Managers.orchestration.loader_main_service": "oaGui.Managers.orchestration.loader_main_service",
    "oaGui.Managers.orchestration.loader_service_composer": "oaGui.Managers.orchestration.loader_service_composer",
    "oaGui.Managers.lifecycle.loader_shutdown_service": "oaGui.Managers.lifecycle.loader_shutdown_service",
    "oaGui.Managers.tabs.tab_orchestrator": "oaGui.Managers.tabs.tab_orchestrator",
    "oaGui.Managers.display.tab_window_manager": "oaGui.Managers.display.tab_window_manager",
    
    # Methods
    "oaGui.Methods.discovery.folder_path_resolver": "oaGui.Methods.discovery.folder_path_resolver",
    "oaGui.Methods.discovery.ui_resource_manager": "oaGui.Methods.discovery.ui_resource_manager",
    "oaGui.Methods.formatting.array_data_expander": "oaGui.Methods.formatting.array_data_expander",
    "oaGui.Methods.formatting.i18n_utils": "oaGui.Methods.formatting.i18n_utils",
    "oaGui.Methods.formatting.ui_coordinate_utils": "oaGui.Methods.formatting.ui_coordinate_utils",
    "oaGui.Methods.formatting.ui_window_geometry_utils": "oaGui.Methods.formatting.ui_window_geometry_utils",
    "oaGui.Methods.processing.blueprint_data_injector": "oaGui.Methods.processing.blueprint_data_injector",
    "oaGui.Methods.processing.blueprint_merger": "oaGui.Methods.processing.blueprint_merger",
    "oaGui.Methods.processing.deferred_task_handler": "oaGui.Methods.processing.deferred_task_handler",
    "oaGui.Methods.processing.transparency_config_parser": "oaGui.Methods.processing.transparency_config_parser",
    "oaGui.Methods.rendering.button_image_renderer": "oaGui.Methods.rendering.button_image_renderer",
    "oaGui.Methods.rendering.grid_column_configurator": "oaGui.Methods.rendering.grid_column_configurator",
    "oaGui.Methods.rendering.grid_renderer_utils": "oaGui.Methods.rendering.grid_renderer_utils",
    "oaGui.Methods.rendering.horizontal_fader_renderer": "oaGui.Methods.rendering.horizontal_fader_renderer",
    "oaGui.Methods.validation.json_integrity_validator": "oaGui.Methods.validation.json_integrity_validator",
    "oaGui.Methods.validation.json_schema_normalizer": "oaGui.Methods.validation.json_schema_normalizer",
    "oaGui.Methods.instrumentation.active_marker_tune_and_collect": "oaGui.Methods.instrumentation.active_marker_tune_and_collect",
    "oaGui.Methods.instrumentation.active_peak_publisher": "oaGui.Methods.instrumentation.active_peak_publisher",
    "oaGui.Methods.instrumentation.marker_logic": "oaGui.Methods.instrumentation.marker_logic",
    "oaGui.Methods.instrumentation.marker_peak_re_publisher": "oaGui.Methods.instrumentation.marker_peak_re_publisher",
    "oaGui.Methods.instrumentation.marker_repository_watcher": "oaGui.Methods.instrumentation.marker_repository_watcher",
    "oaGui.Methods.instrumentation.telemetry_publisher": "oaGui.Methods.instrumentation.telemetry_publisher",
    "oaGui.Methods.execution.engine_destruction_service": "oaGui.Methods.execution.engine_destruction_service",
    "oaGui.Methods.execution.loader_python_engine": "oaGui.Methods.execution.loader_python_engine",
    "oaGui.Methods.execution.loader_signal_handler": "oaGui.Methods.execution.loader_signal_handler",
    "oaGui.Methods.execution.tuning_helpers": "oaGui.Methods.execution.tuning_helpers",
    
    # FileReaders
    "oaGui.FileReaders.scanner.folder_fast_io_utility": "oaGui.FileReaders.scanner.folder_fast_io_utility",
    "oaGui.FileReaders.scanner.folder_layout_interpreter": "oaGui.FileReaders.scanner.folder_layout_interpreter",
    "oaGui.FileReaders.scanner.folder_recursive_scanner": "oaGui.FileReaders.scanner.folder_recursive_scanner",
    "oaGui.FileReaders.loader.gui_file_loader": "oaGui.FileReaders.loader.gui_file_loader",
    "oaGui.FileReaders.loader.json_blueprint_reader": "oaGui.FileReaders.loader.json_blueprint_reader",
    "oaGui.FileReaders.loader.json_gui_host": "oaGui.FileReaders.loader.json_gui_host",
    "oaGui.FileReaders.loader.loader_facade": "oaGui.FileReaders.loader.loader_facade",
    
    # Hooks
    "oaGui.Hooks.registry.registry_widget_store": "oaGui.Hooks.registry.registry_widget_store",
    "oaGui.Hooks.registry.gui_widget_factory": "oaGui.Hooks.registry.gui_widget_factory",
    "oaGui.Hooks.events.interaction_dispatcher": "oaGui.Hooks.events.interaction_dispatcher",
    "oaGui.Hooks.events.interaction_mqtt_gateway": "oaGui.Hooks.events.interaction_mqtt_gateway",
    "oaGui.Hooks.events.mqtt_rebuild_handler": "oaGui.Hooks.events.mqtt_rebuild_handler",
    "oaGui.Hooks.events.telemetry_hooks": "oaGui.Hooks.events.telemetry_hooks",
    "oaGui.Hooks.menu.context_menu": "oaGui.Hooks.menu.context_menu",
    
    # Interface
    "oaGui.Interface.controls.auto_scrollbar": "oaGui.Interface.controls.auto_scrollbar",
    "oaGui.Interface.controls.top_toolbar": "oaGui.Interface.controls.top_toolbar",
    "oaGui.Interface.viewport.Canvas_Viewport_Manager": "oaGui.Interface.viewport.Canvas_Viewport_Manager",
    "oaGui.Interface.viewport.tab_physical_window": "oaGui.Interface.viewport.tab_physical_window",
    "oaGui.Interface.viewport.builder_footer": "oaGui.Interface.viewport.builder_footer",
    "oaGui.Interface.math.coordinate_transformer": "oaGui.Interface.math.coordinate_transformer",
}

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Update full module paths (most specific first)
    sorted_mapping = sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True)
    for old, new in sorted_mapping:
        content = content.replace(old, new)
    
    # 2. Handle cases where they import from parent or sibling (harder to catch generally)
    # But usually full paths are used in this project.
        
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {file_path}")

def main():
    ignore_dirs = {'.git', '.venv', '__pycache__', '.crawler', '.pytest_cache'}
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('oaData')]
        for file in files:
            if file.endswith('.py') or file.endswith('.md') or file.endswith('.json'):
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
