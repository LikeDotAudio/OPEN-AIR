# oaGui/Workers/orchestration/builder_initializer.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Handles initialization and service bootstrapping for LoaderOrchestrator.

from pathlib import Path

from oaConfigurationManager.FileReaders.config_reader import Config
from oaGui.Core.telemetry.interaction_telemetry_service import InteractionTelemetryService
from oaGui.Managers.layout.builder_layout_manager import BuilderLayoutManager


class BuilderInitializer:
    """Handles internal state and service initialization for the UI Orchestrator."""

    @staticmethod
    def initialize_state(orchestrator, path, tab_name, config, parent_builder):
        """Standardizes internal variables and engine references."""
        orchestrator.tab_name = tab_name
        orchestrator.json_filepath = Path(path) if path else None
        orchestrator.state_mirror_engine = config.get("state_mirror_engine")
        orchestrator.subscriber_router = config.get("subscriber_router")
        orchestrator.app_instance = config.get("app_instance")
        orchestrator.on_focus_widget = config.get("on_focus_widget")
        orchestrator.is_editor = config.get("is_editor", False)
        orchestrator.allow_horizontal_scroll = config.get("allow_horizontal_scroll", True)
        orchestrator.allow_scrolling = config.get("allow_scrolling", True)
        orchestrator.is_transparent = config.get("transparent", False) or (parent_builder is not None)
        orchestrator._render_tier = config.get("render_tier", "high_res")

        orchestrator.configuration = {}
        orchestrator.tk_vars = {}
        orchestrator.topic_widgets = {}
        orchestrator._slicing_registry = []
        orchestrator._is_rebuilding = False
        orchestrator.last_build_hash = None
        orchestrator.gui_built = False

    @staticmethod
    def initialize_services(orchestrator, config):
        """Bootstraps telemetry and communication services."""
        orchestrator.tracking_service = InteractionTelemetryService()
        orchestrator._initialize_mqtt_context(
            orchestrator.json_filepath,
            Config.get_instance(),
            config.get("base_mqtt_topic_from_path")
        )
        orchestrator._initialize_widget_factory()
        orchestrator.layout_manager = BuilderLayoutManager(orchestrator)
        orchestrator.tracking_service.track(
            orchestrator,
            orchestrator.tab_name,
            orchestrator.state_mirror_engine,
            orchestrator.base_mqtt_topic_from_path
        )
