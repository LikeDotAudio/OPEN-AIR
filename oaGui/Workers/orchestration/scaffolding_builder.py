# oaGui/Workers/orchestration/scaffolding_builder.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Orchestrates the physical container hierarchy construction for LoaderOrchestrator.

import tkinter as tk
from oaStyle.Core.style import DEFAULT_THEME, THEMES
from oaConfigurationManager.FileReaders.config_reader import Config
from oaGui.Interface.viewport.Canvas_Viewport_Manager import CanvasViewportManager
from oaGui.Interface.controls.auto_scrollbar import AutoScrollbar
from oaGui.Interface.viewport.builder_footer import BuilderFooter
from oaGui.Workers.compositing.engine_visual_effects import EngineVisualEffects
from oaGuiEditorWYSIWYG.Methods.builder_editor_grid import BuilderEditorGrid

class ScaffoldingBuilder:
    """Orchestrates the physical container hierarchy construction."""

    @staticmethod
    def build(orchestrator, use_grid):
        """Constructs the core frame/canvas structure."""
        theme = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        orchestrator.config(bg=theme["bg"])
        orchestrator.grid_rowconfigure(0, weight=1); orchestrator.grid_columnconfigure(0, weight=1)

        ScaffoldingBuilder._setup_main_container(orchestrator, theme["bg"])
        ScaffoldingBuilder._setup_scroll_system(orchestrator, theme["bg"])
        ScaffoldingBuilder._setup_footer_bar(orchestrator)
        ScaffoldingBuilder._apply_initial_transparency(orchestrator)
        
        if orchestrator.canvas and orchestrator.is_editor: 
            BuilderEditorGrid.draw(orchestrator.canvas, orchestrator.scroll_frame, True)

    @staticmethod
    def _setup_main_container(orchestrator, bg):
        """Creates the primary content frame."""
        orchestrator.main_content_frame = tk.Frame(orchestrator, bg=bg, bd=0, highlightthickness=0)
        orchestrator.main_content_frame.grid(row=0, column=0, sticky="nsew")
        orchestrator.main_content_frame.grid_rowconfigure(0, weight=1)
        orchestrator.main_content_frame.grid_columnconfigure(0, weight=1)

    @staticmethod
    def _setup_scroll_system(orchestrator, bg):
        """Configures the canvas-based scrolling system or fallback static frame."""
        if orchestrator.allow_scrolling:
            orchestrator.viewport_manager = CanvasViewportManager(
                orchestrator.main_content_frame, bg, orchestrator.allow_horizontal_scroll
            )
            
            orchestrator.canvas = orchestrator.viewport_manager.canvas
            orchestrator.scroll_frame = orchestrator.viewport_manager.scroll_frame
            orchestrator.canvas_window_id = orchestrator.viewport_manager.window_id

            ScaffoldingBuilder._setup_scrolling_controls(orchestrator)
            orchestrator._setup_event_bindings()
            orchestrator.canvas.grid(row=0, column=0, sticky="nsew")
        else:
            orchestrator.scroll_frame = tk.Frame(orchestrator.main_content_frame, bd=0, highlightthickness=0, bg=bg)
            orchestrator.scroll_frame.grid(row=0, column=0, sticky="nsew")
            orchestrator.canvas, orchestrator.canvas_window_id, orchestrator.viewport_manager = None, None, None
            orchestrator.scroll_frame.bind("<Configure>", lambda e: orchestrator._trigger_background_sync())

    @staticmethod
    def _setup_scrolling_controls(orchestrator):
        """Wires up the industrial scrollbars to the canvas."""
        orchestrator.scrollbar_v = AutoScrollbar(orchestrator.main_content_frame, orient=tk.VERTICAL, command=orchestrator.canvas.yview)
        orchestrator.canvas.configure(yscrollcommand=orchestrator._on_scroll_v)
        orchestrator.scrollbar_v.grid(row=0, column=1, sticky="ns")

        if orchestrator.allow_horizontal_scroll:
            orchestrator.scrollbar_h = AutoScrollbar(orchestrator.main_content_frame, orient=tk.HORIZONTAL, command=orchestrator.canvas.xview)
            orchestrator.canvas.configure(xscrollcommand=orchestrator._on_scroll_h)
            orchestrator.scrollbar_h.grid(row=1, column=0, sticky="ew")

    @staticmethod
    def _setup_footer_bar(orchestrator):
        """Integrates the builder footer if enabled in configuration."""
        if getattr(Config.get_instance(), 'FOOTER_ENABLED', False):
            orchestrator.footer = BuilderFooter(orchestrator.main_content_frame)
            orchestrator.footer.grid(row=2, column=0, columnspan=2, sticky="ew")
        else:
            orchestrator.footer = None

    @staticmethod
    def _apply_initial_transparency(orchestrator):
        """Applies high-res transparency layers to core scaffolding."""
        if not orchestrator.is_transparent or not orchestrator.parent_builder: return
        EngineVisualEffects.apply_transparency(orchestrator.main_content_frame, None, {"type": "OcaBlock"}, orchestrator.parent_builder)
        if orchestrator.canvas:
            EngineVisualEffects.apply_transparency(orchestrator.canvas, orchestrator.canvas, {"type": "OcaBin"}, orchestrator.parent_builder)
        EngineVisualEffects.apply_transparency(orchestrator.scroll_frame, None, {"type": "OcaBlock"}, orchestrator.parent_builder)
