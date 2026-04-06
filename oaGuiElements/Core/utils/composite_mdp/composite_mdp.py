# composite_mdp/composite_mdp.py
from oaGuiFramework.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized Motion Draggable Potentiometer (MDP).

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from loguru import logger

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import builder_logger
from oaConfigurationManager.FileReaders.config_reader import Config
app_constants = Config.get_instance()

from oaGuiElements.Core.graphing.graphing.dynamic_graph import GraphPlotter
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

# --- EXTRACTED CORE MODULES ---
from .Core.mdp_ltp_component import MDPLTPComponent
from .Core.mdp_interaction_mixin import MDPInteractionMixin

class MDPFrame(tk.Frame, TransparencyMixin):
    def __init__(self, master, builder_instance=None, config=None, **kwargs):
        super().__init__(master, **kwargs)
        self.widget_config, self.faders = config, []
        self.active_fader = self.hovered_fader = None

@WidgetRegistry.register("_MDP")
class BuilderCompositeMdpCreator(TransparencyMixin, MDPInteractionMixin):
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️🕹️ [BUILDER] Creating MDP widget.", level="TRACE")
        
        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = ctx.builder_instance if hasattr(ctx, 'builder_instance') else ctx.app_instance
        
        mdp_frame = MDPFrame(parent_widget, builder_instance=b_inst, config=config_data)
        
        # 1. Graph Background
        g_cfg = config_data.get("graph", {"show_grid": True, "xlim": [0, 10], "ylim": [0, 10]})
        plotter = GraphPlotter(mdp_frame, g_cfg, ctx.base_mqtt_topic_from_path, f"{config_data.get('path')}/graph", 
                              subscriber_router=ctx.subscriber_router, state_mirror_engine=ctx.state_mirror_engine, builder_instance=b_inst)
        plotter.pack(fill=tk.BOTH, expand=True)
        
        tk_canvas = plotter.canvas.get_tk_widget()
        if hasattr(b_inst, '_apply_transparency'): b_inst._apply_transparency(mdp_frame, tk_canvas, config_data, b_inst)
        
        def redraw():
            for item in tk_canvas.find_all():
                if "panel_bg_slice" not in tk_canvas.gettags(item): tk_canvas.delete(item)
            for f in mdp_frame.faders: f.render()
        mdp_frame._draw = redraw
        
        # 2. Floating LTP Vector
        ltp_cfg = config_data.get("ltp", {}); path = config_data.get("path", ""); ltp_path = f"{path}/ltp"
        lin_var = tk.DoubleVar(value=float(ltp_cfg.get("value_default", 50.0)))
        rot_var = tk.DoubleVar(value=float(ltp_cfg.get("rotation_default", 0.0)))
        
        if ctx.state_mirror_engine:
            ctx.state_mirror_engine.register_widget(ltp_path, lin_var, ctx.base_mqtt_topic_from_path, ltp_cfg)
            ctx.state_mirror_engine.initialize_widget_state(ltp_path)
            lin_var.trace_add("write", lambda *a: ctx.state_mirror_engine.broadcast_gui_change_to_mqtt(ltp_path))
            
            r_path = f"{ltp_path}/rotation"
            ctx.state_mirror_engine.register_widget(r_path, rot_var, ctx.base_mqtt_topic_from_path, ltp_cfg)
            ctx.state_mirror_engine.initialize_widget_state(r_path)
            rot_var.trace_add("write", lambda *a: ctx.state_mirror_engine.broadcast_gui_change_to_mqtt(r_path))

        fader = MDPLTPComponent(tk_canvas, "0", config_data.get("initial_x", 150), config_data.get("initial_y", 150), lin_var, rot_var, ltp_cfg)
        mdp_frame.faders.append(fader)
        
        # 3. Bindings
        tk_canvas.bind("<Button-1>", lambda e: BuilderCompositeMdpCreator._mdp_on_click(e, mdp_frame), add="+")
        tk_canvas.bind("<B1-Motion>", lambda e: BuilderCompositeMdpCreator._mdp_on_drag(e, mdp_frame), add="+")
        tk_canvas.bind("<ButtonRelease-1>", lambda e: BuilderCompositeMdpCreator._mdp_on_release(e, mdp_frame), add="+")
        tk_canvas.bind("<Button-2>", lambda e: BuilderCompositeMdpCreator._mdp_on_mid_click(e, mdp_frame), add="+")
        tk_canvas.bind("<B2-Motion>", lambda e: BuilderCompositeMdpCreator._mdp_on_mid_drag(e, mdp_frame), add="+")
        tk_canvas.bind("<ButtonRelease-2>", lambda e: BuilderCompositeMdpCreator._mdp_on_release(e, mdp_frame), add="+")
        tk_canvas.bind("<MouseWheel>", lambda e: BuilderCompositeMdpCreator._mdp_on_scroll(e, mdp_frame), add="+")
        tk_canvas.bind("<Button-4>", lambda e: BuilderCompositeMdpCreator._mdp_on_scroll(e, mdp_frame), add="+")
        tk_canvas.bind("<Button-5>", lambda e: BuilderCompositeMdpCreator._mdp_on_scroll(e, mdp_frame), add="+")
        tk_canvas.bind("<Motion>", lambda e: BuilderCompositeMdpCreator._mdp_on_motion(e, mdp_frame), add="+")
        
        return mdp_frame

    def make_composite_mdp(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderCompositeMdpCreator.make(parent_widget, config_data, context, builder_instance=self, **kwargs)