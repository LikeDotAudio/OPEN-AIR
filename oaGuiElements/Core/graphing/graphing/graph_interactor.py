# graphing/graph_interactor.py
from oaGuiFramework.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized Graph Interactor Engine.

from typing import Dict, Any
from oaLogging.Methods.matrix_gate import matrix_log
import inspect

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import builder_logger
from loguru import logger

# --- EXTRACTED CORE MODULES ---
from .Core.annotation import AnnotationManager
from .Core.view_controller import ViewController
from .Core.graph_context_menu import GraphContextMenu

def setup_interaction(fig: object, ax: object, interaction_config: Dict[str, Any], callbacks: Dict[str, Any] = None):
    """Initializes interactive features (Zoom, Pan, Hover, Context Menu) for a figure."""
    try:
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔬🏗️📊 [BUILDER] graph_interactor: Initializing interaction protocols.", level="DEBUG")
        
        nav_cfg = interaction_config.get("Navigation", interaction_config)
        
        # 1. Hover Annotations
        annot = None
        if nav_cfg.get("show_hover_value"):
            ax._hover_vline = ax.axvline(0, color='grey', ls='--', lw=1, alpha=0.7, visible=False, zorder=1)
            ax._hover_dots = [ax.plot([], [], 'o', ms=6, visible=False, zorder=10)[0] for _ in range(10)]
            annot = ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points", 
                                bbox=dict(boxstyle="round", fc="w", alpha=0.9), arrowprops=dict(arrowstyle="->"), zorder=11)
            annot.set_visible(False); ax.hover_enabled = True
            fig.canvas.mpl_connect("motion_notify_event", lambda e: AnnotationManager.update(e, ax, annot))

        # 2. Zoom & Pan
        if nav_cfg.get("enable_zoom") or nav_cfg.get("enable_pan"):
            def on_cm(e): GraphContextMenu.show(e, fig, ax, annot, callbacks)
            ax.zoom_pan = ViewController(ax, callbacks, on_cm)
            
            # Map event connections
            fig.canvas.mpl_connect("button_press_event", ax.zoom_pan.on_press)
            fig.canvas.mpl_connect("button_release_event", ax.zoom_pan.on_release)
            fig.canvas.mpl_connect("motion_notify_event", ax.zoom_pan.on_motion)
            fig.canvas.mpl_connect("scroll_event", ax.zoom_pan.on_scroll)

    except Exception as e:
        logger.exception(f"❌ Graph Interactor: Setup failed - {e}")

def update_annotation(event, ax, annot):
    """Backwards compatibility wrapper for AnnotationManager."""
    AnnotationManager.update(event, ax, annot)

class ZoomPan(ViewController):
    """Backwards compatibility wrapper for ViewController."""
    pass