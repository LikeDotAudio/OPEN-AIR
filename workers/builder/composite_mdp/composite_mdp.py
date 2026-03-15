# composite_mdp/MDP/MDP_Widget.py
import tkinter as tk
import math
from workers.builder.data_graphing.dynamic_graph import FluxPlotter

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from managers.Display.transparency.transparency_mixin import TransparencyMixin

class LTPObject:
    """
    Unbounded Floating Linear Traveling Potentiometer (LTP) drawn on a Canvas.
    Supports linear slide, rotary knob, widget rotation, and moving.
    """
    def __init__(self, canvas, widget_id, x, y, linear_var, rotation_var, config):
        self.canvas = canvas
        self.widget_id = widget_id
        self.x = x
        self.y = y
        self.angle = 0.0
        
        # State Variables (Tkinter Vars for MQTT integration)
        self.linear_var = linear_var
        self.rotation_var = rotation_var
        
        # Configuration
        self.val_min = float(config.get("value_min", 0.0))
        self.val_max = float(config.get("value_max", 100.0))
        self.rot_min = float(config.get("rotation_min", -130.0))
        self.rot_max = float(config.get("rotation_max", 130.0))
        
        # Style
        self.cap_color = "#333333"
        self.cap_outline_normal = "#888888"
        self.cap_outline_hover = "#00ffff"
        self.highlight_color = "#00bfff"
        self.track_len = 200
        
        self.tag_root = f"mdp_ltp_{self.widget_id}"
        
        # Interaction State
        self.dragging = False
        self.hovered = False
        self.start_x = 0
        self.start_y = 0
        self.start_val = 0
        self.start_rot = 0
        self.start_pos = (0, 0)
        
        # Trace variables to update redraw (Sync from MQTT)
        self.linear_var.trace_add("write", self._on_var_change)
        self.rotation_var.trace_add("write", self._on_var_change)
        
        self.render()

    def _on_var_change(self, *args):
        # Trigger redraw when variables change externally
        self.render()

    def rotate_point(self, px, py, cx, cy, angle_deg):
        rad = math.radians(angle_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        nx = cos_a * (px - cx) - sin_a * (py - cy) + cx
        ny = sin_a * (px - cx) + cos_a * (py - cy) + cy
        return nx, ny

    def render(self):
        self.canvas.delete(self.tag_root)
        cx, cy, ang, tl = self.x, self.y, self.angle, self.track_len
        
        # Current Values
        try:
            val_current = float(self.linear_var.get())
            rot_current = float(self.rotation_var.get())
        except ValueError:
            val_current = self.val_min
            rot_current = self.rot_min

        # Hitbox (Transparent polygon)
        hb_w = 60
        hbp = [
            self.rotate_point(cx - hb_w/2, cy - tl/2 - 20, cx, cy, ang),
            self.rotate_point(cx + hb_w/2, cy - tl/2 - 20, cx, cy, ang),
            self.rotate_point(cx + hb_w/2, cy + tl/2 + 20, cx, cy, ang),
            self.rotate_point(cx - hb_w/2, cy + tl/2 + 20, cx, cy, ang)
        ]
        flat_hbp = [coord for pt in hbp for coord in pt]
        self.canvas.create_polygon(flat_hbp, fill="", outline="", tags=(self.tag_root, "hitbox"))

        # Track
        p1 = self.rotate_point(cx, cy - tl/2, cx, cy, ang)
        p2 = self.rotate_point(cx, cy + tl/2, cx, cy, ang)
        self.canvas.create_line(p1, p2, fill="#000000", width=6, capstyle=tk.ROUND, tags=self.tag_root)
        self.canvas.create_line(p1, p2, fill="#222222", width=2, capstyle=tk.ROUND, tags=self.tag_root)
        
        # Ticks
        for i in range(11):
            ly = (cy + tl/2) - (tl * (i/10))
            leng = 10 if i % 5 == 0 else 5
            tp1, tp2 = self.rotate_point(cx-15, ly, cx, cy, ang), self.rotate_point(cx-15-leng, ly, cx, cy, ang)
            self.canvas.create_line(tp1, tp2, fill="#666666", tags=self.tag_root)
            tp3, tp4 = self.rotate_point(cx+15, ly, cx, cy, ang), self.rotate_point(cx+15+leng, ly, cx, cy, ang)
            self.canvas.create_line(tp3, tp4, fill="#666666", tags=self.tag_root)

        # Cap
        denom = (self.val_max - self.val_min)
        norm = (val_current - self.val_min) / denom if denom != 0 else 0
        local_cap_y = (cy + tl/2) - (norm * tl)
        ccx, ccy = self.rotate_point(cx, local_cap_y, cx, cy, ang)
        r = 22
        
        # Hover Glow
        outline_col = self.cap_outline_hover if self.hovered else self.cap_outline_normal
        outline_w = 3 if self.hovered else 2
        
        self.canvas.create_oval(ccx-r, ccy-r, ccx+r, ccy+r, fill=self.cap_color, outline=outline_col, width=outline_w, tags=(self.tag_root, "cap"))
        
        # Pointer
        prad = math.radians(90 - rot_current - ang)
        px, py = ccx + (r-2)*math.cos(prad), ccy - (r-2)*math.sin(prad)
        self.canvas.create_line(ccx, ccy, px, py, fill=self.highlight_color, width=3, capstyle=tk.ROUND, tags=self.tag_root)
        self.canvas.create_oval(ccx-3, ccy-3, ccx+3, ccy+3, fill=self.highlight_color, outline="", tags=self.tag_root)
        
        # Text
        self.canvas.create_text(ccx, ccy-35, text=f"{val_current:.1f}", fill="white", font=("Arial", 8), tags=self.tag_root)
        self.canvas.create_text(ccx, ccy+35, text=f"R:{rot_current:.0f}", fill="#aaaaaa", font=("Arial", 7), tags=self.tag_root)
        # self.canvas.create_text(cx, cy + tl/2 + 30, text=f"ID:{self.widget_id}", fill="#555555", font=("Arial", 8), tags=self.tag_root)

    def set_hover(self, state):
        if self.hovered != state:
            self.hovered = state
            self.render()

    def lift(self):
        self.canvas.tag_raise(self.tag_root)


from managers.Display.factory.widget_registry import WidgetRegistry

class MDPFrame(tk.Frame, TransparencyMixin):
    def __init__(self, master, builder_instance=None, config=None, **kwargs):
        super().__init__(master, **kwargs)
        self.widget_config = config
        self.faders = []
        self.active_fader = None
        self.hovered_fader = None
        
        # Note: FluxPlotter uses a tk.Canvas internally.
        # We'll apply transparency once the plotter is ready.

@WidgetRegistry.register("_MDP")
class BuilderCompositeMdpCreator(TransparencyMixin):
    """Mixin to create a Motion Draggable Potentiometer (MDP) widget."""
    
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """
        Static factory method for creating an MDP widget.
        """
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🕹️ [BUILDER] Entering BuilderCompositeMdpCreator.make")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        label = config_data.get("label_active", "MDP")
        path = config_data.get("path", "")
        
        # ⚡ HARDENED INTERFACE: Extract from context if available
        if BUILDER_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            app_instance = context.app_instance
            builder_instance = context.builder_instance or app_instance
            if BUILDER_DEBUG: builder_logger.debug("✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.")
        else:
            # Fallback for legacy calls (should be phased out)
            state_mirror_engine = kwargs.get("state_mirror_engine")
            subscriber_router = kwargs.get("subscriber_router")
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance")
            app_instance = kwargs.get("app_instance")
            if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to kwargs.")

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️🕹️ [BUILDER] Spawning Motion Draggable Potentiometer for '{label}' at '{path}'.")
        
        base_mqtt_topic = base_mqtt_topic_from_path
        
        # 1. Create Container Frame
        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [CONSTRUCT] Creating MDPFrame container.")
        mdp_frame = MDPFrame(parent_widget, builder_instance=builder_instance, config=config_data)
        
        # 2. Create Background Graph (FluxPlotter)
        graph_config = config_data.get("graph", {
            "title": "MDP Graph", "show_title": False, "show_legend": False,
            "show_grid": True, "xlim": [0, 10], "ylim": [0, 10], "datasets": [] 
        })
        
        if BUILDER_DEBUG: builder_logger.trace(f"🏗️📊📉 [CONSTRUCT] Initializing internal FluxPlotter.")
        plotter = FluxPlotter(
            mdp_frame, 
            graph_config, 
            base_mqtt_topic, 
            f"{path}/graph",
            subscriber_router=subscriber_router,
            state_mirror_engine=state_mirror_engine,
            builder_instance=builder_instance
        )
        plotter.pack(fill=tk.BOTH, expand=True)
        
        # Apply Industrial Transparency to Plotter's Canvas
        tk_canvas = plotter.canvas.get_tk_widget()
        if hasattr(builder_instance, '_apply_transparency'):
            if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to MDP graph canvas.")
            builder_instance._apply_transparency(mdp_frame, tk_canvas, config_data, builder_instance)
        
        # Redraw hook for transparency
        def _mdp_redraw():
            # ⚡ INDUSTRIAL TRANSPARENCY: Don't delete everything, preserve the patina slice
            if BUILDER_DEBUG: builder_logger.trace(f"🔄✨🎨 [REDRAW] Executing MDP frame redraw (syncing transparency).")
            for item in tk_canvas.find_all():
                tags = tk_canvas.gettags(item)
                if "panel_bg_slice" not in tags:
                    tk_canvas.delete(item)
            for f in mdp_frame.faders: f.render()
            
        mdp_frame._draw = _mdp_redraw
        
        # 3. Create Foreground LTP (Floating Vector Object)
        ltp_config = config_data.get("ltp", {})
        ltp_path = f"{path}/ltp"
        
        # Initialize Variables
        linear_var = tk.DoubleVar(value=float(ltp_config.get("value_default", 50.0)))
        rotation_var = tk.DoubleVar(value=float(ltp_config.get("rotation_default", 0.0)))
        if BUILDER_DEBUG: builder_logger.debug(f"🔋🎚️🎛️ [STATE] Initial LTP values: Lin={linear_var.get()}, Rot={rotation_var.get()}")
        
        # Register with State Mirror
        if state_mirror_engine:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering dual LTP state at path '{ltp_path}'")
            # Linear
            state_mirror_engine.register_widget(ltp_path, linear_var, base_mqtt_topic, ltp_config)
            topic = state_mirror_engine.get_widget_topic(ltp_path)
            if subscriber_router and topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing LINEAR to topic: {topic}")
                subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
            
            if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing LINEAR state from cache/broker.")
            state_mirror_engine.initialize_widget_state(ltp_path)
            
            def on_lin_change(*a):
                if BUILDER_DEBUG: builder_logger.trace(f"⚡🔴📡 [EVENT] LTP linear change. Broadcasting to '{ltp_path}'")
                state_mirror_engine.broadcast_gui_change_to_mqtt(ltp_path)
            linear_var.trace_add("write", on_lin_change)
            
            # Rotation
            rot_path = f"{ltp_path}/rotation"
            rot_config = ltp_config.copy()
            rot_config["path"] = rot_path
            state_mirror_engine.register_widget(rot_path, rotation_var, base_mqtt_topic, rot_config)
            rot_topic = state_mirror_engine.get_widget_topic(rot_path)
            if subscriber_router and rot_topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing ROTATION to topic: {rot_topic}")
                subscriber_router.subscribe_to_topic(rot_topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
            
            if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing ROTATION state from cache/broker.")
            state_mirror_engine.initialize_widget_state(rot_path)
            
            def on_rot_change(*a):
                if BUILDER_DEBUG: builder_logger.trace(f"⚡🔴📡 [EVENT] LTP rotation change. Broadcasting to '{rot_path}'")
                state_mirror_engine.broadcast_gui_change_to_mqtt(rot_path)
            rotation_var.trace_add("write", on_rot_change)

        # Create LTP Object on the Plotter's Canvas
        tk_canvas = plotter.canvas.get_tk_widget()
        
        initial_x = config_data.get("initial_x", 150)
        initial_y = config_data.get("initial_y", 150)
        
        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🔳🕹️ [CONSTRUCT] Instantiating floating LTPObject vector handle.")
        fader = LTPObject(tk_canvas, "0", initial_x, initial_y, linear_var, rotation_var, ltp_config)
        mdp_frame.faders.append(fader)
        
        # 4. Bindings (Global Dispatcher on Canvas)
        if BUILDER_DEBUG: builder_logger.trace("🖱️👆🔗 [EVENTS] Binding global MDP dispatcher to plotter canvas.")
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
        
        if BUILDER_DEBUG: builder_logger.success(f"✅🆗🕹️ [SUCCESS] The Motion Draggable Potentiometer '{label}' has materialized!")
        return mdp_frame

    def make_composite_mdp(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderCompositeMdpCreator.make(parent_widget, config_data, context, builder_instance=self, **kwargs)

    # --- Dispatcher Methods (Converted to static) ---

    @staticmethod
    def _mdp_get_fader_at(x, y, frame):
        # We need to search the specific canvas.
        canvas = frame.winfo_children()[0].canvas.get_tk_widget() # Assuming Plotter is first child
        
        item_id = canvas.find_closest(x, y, halo=5)
        if not item_id: return None
        tags = canvas.gettags(item_id[0])
        
        for tag in tags:
            if tag.startswith("mdp_ltp_"):
                return frame.faders[0] # Simplification for single-fader usage
        return None

    @staticmethod
    def _mdp_on_motion(event, frame):
        fader = BuilderCompositeMdpCreator._mdp_get_fader_at(event.x, event.y, frame)
        if fader != frame.hovered_fader:
            if frame.hovered_fader: frame.hovered_fader.set_hover(False)
            if fader: fader.set_hover(True)
            frame.hovered_fader = fader

    @staticmethod
    def _mdp_on_click(event, frame):
        fader = BuilderCompositeMdpCreator._mdp_get_fader_at(event.x, event.y, frame)
        if fader:
            frame.active_fader = fader
            fader.lift()
            fader.dragging = True
            fader.start_x, fader.start_y = event.x, event.y
            try:
                fader.start_val = float(fader.linear_var.get())
                fader.start_rot = float(fader.rotation_var.get())
            except ValueError:
                fader.start_val, fader.start_rot = fader.val_min, fader.rot_min

    @staticmethod
    def _mdp_on_drag(event, frame):
        fader = frame.active_fader
        if fader and fader.dragging:
            dx, dy = event.x - fader.start_x, event.y - fader.start_y
            rad = math.radians(fader.angle)
            ldx = dx * math.cos(-rad) - dy * math.sin(-rad)
            ldy = dx * math.sin(-rad) + dy * math.cos(-rad)
            
            # Linear (Vertical drag in local space)
            dv = -(ldy / fader.track_len) * (fader.val_max - fader.val_min)
            new_val = max(fader.val_min, min(fader.val_max, fader.start_val + dv))
            fader.linear_var.set(new_val)
            
            # Rotary (Horizontal drag in local space)
            rot_sens = 1.0
            new_rot = max(fader.rot_min, min(fader.rot_max, fader.start_rot + (ldx * rot_sens)))
            fader.rotation_var.set(new_rot)

    @staticmethod
    def _mdp_on_mid_click(event, frame):
        fader = BuilderCompositeMdpCreator._mdp_get_fader_at(event.x, event.y, frame)
        if fader:
            frame.active_fader = fader
            fader.lift()
            fader.dragging = True
            fader.start_x, fader.start_y = event.x, event.y
            fader.start_pos = (fader.x, fader.y)

    @staticmethod
    def _mdp_on_mid_drag(event, frame):
        fader = frame.active_fader
        if fader and fader.dragging:
            dx, dy = event.x - fader.start_x, event.y - fader.start_y
            fader.x = fader.start_pos[0] + dx
            fader.y = fader.start_pos[1] + dy
            fader.render()

    @staticmethod
    def _mdp_on_release(event, frame):
        if frame.active_fader:
            frame.active_fader.dragging = False
            frame.active_fader = None

    @staticmethod
    def _mdp_on_scroll(event, frame):
        fader = BuilderCompositeMdpCreator._mdp_get_fader_at(event.x, event.y, frame)
        if fader:
            delta = 0
            if event.num == 4: delta = 1
            elif event.num == 5: delta = -1
            elif hasattr(event, "delta"): delta = 1 if event.delta > 0 else -1
            
            if event.state & 0x0008: # Alt + Scroll -> Rotate Widget
                fader.angle += delta * 3
                fader.render()
            else: # Knob Value
                curr = float(fader.rotation_var.get())
                new_rot = max(fader.rot_min, min(fader.rot_max, curr + delta * 3))
                fader.rotation_var.set(new_rot)
