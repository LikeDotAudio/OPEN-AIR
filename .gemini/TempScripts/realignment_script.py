import os
import re

# Comprehensive mapping for all realignment changes
mapping = {
    "oaGui.Managers.orchestration.loader_main_service": "oaGui.Managers.orchestration.loader_main_service",
    "oaGui.Workers.orchestration.loader_orchestrator": "oaGui.Workers.orchestration.loader_orchestrator",
    "oaGui.Managers.bootstrap.loader_bootstrap_engine": "oaGui.Managers.bootstrap.loader_bootstrap_engine",
    "oaGui.Managers.orchestration.loader_service_composer": "oaGui.Managers.orchestration.loader_service_composer",
    "oaGui.FileReaders.loader.loader_facade": "oaGui.FileReaders.loader.loader_facade",
    "oaGui.Methods.execution.loader_python_engine": "oaGui.Methods.execution.loader_python_engine",
    "oaGui.Managers.lifecycle.loader_lifecycle_service": "oaGui.Managers.lifecycle.loader_lifecycle_service",
    "oaGui.Managers.lifecycle.loader_shutdown_service": "oaGui.Managers.lifecycle.loader_shutdown_service",
    "oaGui.Methods.execution.loader_signal_handler": "oaGui.Methods.execution.loader_signal_handler",
    "oaGui.FileReaders.scanner.folder_recursive_scanner": "oaGui.FileReaders.scanner.folder_recursive_scanner",
    "oaGui.FileReaders.scanner.folder_layout_interpreter": "oaGui.FileReaders.scanner.folder_layout_interpreter",
    "oaGui.FileReaders.scanner.folder_fast_io_utility": "oaGui.FileReaders.scanner.folder_fast_io_utility",
    "oaGui.Methods.discovery.folder_path_resolver": "oaGui.Methods.discovery.folder_path_resolver",
    "oaGui.Managers.tabs.tab_orchestrator": "oaGui.Managers.tabs.tab_orchestrator",
    "oaGui.Managers.display.tab_window_manager": "oaGui.Managers.display.tab_window_manager",
    "oaGui.Interface.viewport.tab_physical_window": "oaGui.Interface.viewport.tab_physical_window",
    "oaGui.FileReaders.loader.json_blueprint_reader": "oaGui.FileReaders.loader.json_blueprint_reader",
    "oaGui.FileReaders.loader.json_gui_host": "oaGui.FileReaders.loader.json_gui_host",
    "oaGui.FileReaders.standardizers.json_schema_harmonizer": "oaGui.FileReaders.standardizers.json_schema_harmonizer",
    "oaGui.FileReaders.standardizers.json_shorthand_resolver": "oaGui.FileReaders.standardizers.json_shorthand_resolver",
    "oaGui.Methods.validation.json_integrity_validator": "oaGui.Methods.validation.json_integrity_validator",
    "oaGui.Methods.validation.json_schema_normalizer": "oaGui.Methods.validation.json_schema_normalizer",
    "oaGui.Hooks.registry.registry_widget_store": "oaGui.Hooks.registry.registry_widget_store",
    "oaGui.Managers.persistence.cache_layout_store": "oaGui.Managers.persistence.cache_layout_store",
    "oaGui.Managers.persistence.cache_blueprint_store": "oaGui.Managers.persistence.cache_blueprint_store",
    "oaGui.Core.factory.cache_image_store": "oaGui.Core.factory.cache_image_store",
    "oaGui.Core.context.cache_widget_context": "oaGui.Core.context.cache_widget_context",
    "oaGui.Workers.scheduling.engine_render_scheduler": "oaGui.Workers.scheduling.engine_render_scheduler",
    "oaGui.Managers.assembler.engine_widget_assembler": "oaGui.Managers.assembler.engine_widget_assembler",
    "oaGui.Managers.grid.engine_grid_layout_logic": "oaGui.Managers.grid.engine_grid_layout_logic",
    "oaGui.Workers.compositing.engine_visual_effects": "oaGui.Workers.compositing.engine_visual_effects",
    "oaGui.Workers.compositing.engine_texture_mapper": "oaGui.Workers.compositing.engine_texture_mapper",
    "oaGui.Managers.refresh.engine_refresh_coordinator": "oaGui.Managers.refresh.engine_refresh_coordinator",
    "oaGui.Managers.assembler.engine_widget_instantiator": "oaGui.Managers.assembler.engine_widget_instantiator",
    "oaGui.Managers.display.engine_gui_display": "oaGui.Managers.display.engine_gui_display",
    "oaGui.Workers.assembly.engine_structural_assembler": "oaGui.Workers.assembly.engine_structural_assembler",
    "oaGui.Methods.execution.engine_destruction_service": "oaGui.Methods.execution.engine_destruction_service",
    "oaGui.Managers.interaction.interaction_navigation": "oaGui.Managers.interaction.interaction_navigation",
    "oaGui.Managers.interaction.interaction_view_states": "oaGui.Managers.interaction.interaction_view_states",
    "oaGui.Hooks.events.interaction_dispatcher": "oaGui.Hooks.events.interaction_dispatcher",
    "oaGui.Hooks.events.interaction_mqtt_gateway": "oaGui.Hooks.events.interaction_mqtt_gateway",
    "oaGui.Core.telemetry.interaction_telemetry_service": "oaGui.Core.telemetry.interaction_telemetry_service"
}

# Module and file name replacements (without paths)
base_mapping = {
    "loader_main_service": "loader_main_service",
    "loader_orchestrator": "loader_orchestrator",
    "loader_bootstrap_engine": "loader_bootstrap_engine",
    "loader_service_composer": "loader_service_composer",
    "loader_facade": "loader_facade",
    "loader_python_engine": "loader_python_engine",
    "loader_lifecycle_service": "loader_lifecycle_service",
    "loader_shutdown_service": "loader_shutdown_service",
    "loader_signal_handler": "loader_signal_handler",
    "folder_recursive_scanner": "folder_recursive_scanner",
    "folder_layout_interpreter": "folder_layout_interpreter",
    "folder_fast_io_utility": "folder_fast_io_utility",
    "folder_path_resolver": "folder_path_resolver",
    "tab_orchestrator": "tab_orchestrator",
    "tab_window_manager": "tab_window_manager",
    "tab_physical_window": "tab_physical_window",
    "json_blueprint_reader": "json_blueprint_reader",
    "json_gui_host": "json_gui_host",
    "json_schema_harmonizer": "json_schema_harmonizer",
    "json_shorthand_resolver": "json_shorthand_resolver",
    "json_integrity_validator": "json_integrity_validator",
    "json_schema_normalizer": "json_schema_normalizer",
    "registry_widget_store": "registry_widget_store",
    "cache_layout_store": "cache_layout_store",
    "cache_blueprint_store": "cache_blueprint_store",
    "cache_image_store": "cache_image_store",
    "cache_widget_context": "cache_widget_context",
    "engine_render_scheduler": "engine_render_scheduler",
    "engine_widget_assembler": "engine_widget_assembler",
    "engine_grid_layout_logic": "engine_grid_layout_logic",
    "engine_visual_effects": "engine_visual_effects",
    "engine_texture_mapper": "engine_texture_mapper",
    "engine_refresh_coordinator": "engine_refresh_coordinator",
    "engine_widget_instantiator": "engine_widget_instantiator",
    "engine_gui_display": "engine_gui_display",
    "engine_structural_assembler": "engine_structural_assembler",
    "engine_destruction_service": "engine_destruction_service",
    "interaction_navigation": "interaction_navigation",
    "interaction_view_states": "interaction_view_states",
    "interaction_dispatcher": "interaction_dispatcher",
    "interaction_mqtt_gateway": "interaction_mqtt_gateway",
    "interaction_telemetry_service": "interaction_telemetry_service"
}

class_mapping = {
    "FolderRecursiveScannerMixin": "FolderRecursiveScannerMixin",
    "FolderLayoutInterpreter": "FolderLayoutInterpreter",
    "EngineWidgetAssemblerMixin": "EngineWidgetAssemblerMixin",
    "EngineGuiDisplay": "EngineGuiDisplay",
    "InteractionMqttGatewayMixin": "InteractionMqttGatewayMixin",
    "LoaderOrchestrator": "LoaderOrchestrator",
    "LoaderBootstrapEngine": "LoaderBootstrapEngine",
    "LoaderServiceComposer": "LoaderServiceComposer",
    "LoaderFacade": "LoaderFacade",
    "LoaderPythonEngine": "LoaderPythonEngine",
    "JsonBlueprintReader": "JsonBlueprintReader",
    "JsonGuiHost": "JsonGuiHost",
    "JsonShorthandResolver": "JsonShorthandResolver",
    "JsonIntegrityValidator": "JsonIntegrityValidator",
    "JsonSchemaNormalizer": "JsonSchemaNormalizer",
    "RegistryWidgetStore": "RegistryWidgetStore",
    "CacheLayoutStore": "CacheLayoutStore",
    "CacheBlueprintStore": "CacheBlueprintStore",
    "CacheImageStore": "CacheImageStore",
    "EngineRenderScheduler": "EngineRenderScheduler",
    "EngineVisualEffects": "EngineVisualEffects",
    "EngineTextureMapper": "EngineTextureMapper",
    "EngineRefreshCoordinator": "EngineRefreshCoordinator",
    "InteractionNavigationMixin": "InteractionNavigationMixin",
    "InteractionViewStates": "InteractionViewStates",
    "InteractionDispatcher": "InteractionDispatcher",
    "InteractionTelemetryService": "InteractionTelemetryService",
    "LoaderShutdownService": "LoaderShutdownService",
    "LoaderLifecycleService": "LoaderLifecycleService",
    "LoaderSignalHandler": "LoaderSignalHandler",
    "TabWindowManager": "TabWindowManager",
    "TabOrchestratorMixin": "TabOrchestratorMixin",
    "TabWindowManager": "TabWindowManager"
}

def process_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Update full module paths (most specific first)
    for old, new in mapping.items():
        content = content.replace(old, new)
    
    # 2. Update base module names and file names with word boundaries
    for old, new in base_mapping.items():
        # Handle .py extension separately or together? Together is safer.
        content = content.replace(old + ".py", new + ".py")
        # For modules in imports like 'from .engine_visual_effects import'
        content = re.sub(r'\b' + old + r'\b', new, content)
    
    # 3. Update Class Names with word boundaries
    for old, new in class_mapping.items():
        content = re.sub(r'\b' + old + r'\b', new, content)
        
    if content != original_content:
        with open(file_path, 'w') as f:
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
