import math
from .mdp_math import MDPMath

class MDPInteractionMixin:
    """Static interaction handlers for dispatching MDP events to fader components."""

    @staticmethod
    def _mdp_get_fader_at(x, y, frame):
        # Access the plotter's canvas
        canvas = frame.winfo_children()[0].canvas.get_tk_widget()
        item_id = canvas.find_closest(x, y, halo=5)
        if not item_id: return None
        tags = canvas.gettags(item_id[0])
        for tag in tags:
            if tag.startswith("mdp_ltp_"): return frame.faders[0] 
        return None

    @staticmethod
    def _mdp_on_motion(event, frame):
        f = MDPInteractionMixin._mdp_get_fader_at(event.x, event.y, frame)
        if f != frame.hovered_fader:
            if frame.hovered_fader: frame.hovered_fader.set_hover(False)
            if f: f.set_hover(True)
            frame.hovered_fader = f

    @staticmethod
    def _mdp_on_click(event, frame):
        f = MDPInteractionMixin._mdp_get_fader_at(event.x, event.y, frame)
        if f:
            frame.active_fader = f; f.lift(); f.dragging = True
            f.start_x, f.start_y = event.x, event.y
            try: f.start_val, f.start_rot = float(f.linear_var.get()), float(f.rotation_var.get())
            except: f.start_val, f.start_rot = f.val_min, f.rot_min

    @staticmethod
    def _mdp_on_drag(event, frame):
        f = frame.active_fader
        if f and f.dragging:
            dx, dy = event.x - f.start_x, event.y - f.start_y
            ldx, ldy = MDPMath.to_local_space(dx, dy, f.angle)
            
            # Linear (Local Y)
            dv = -(ldy / f.track_len) * (f.val_max - f.val_min)
            f.linear_var.set(max(f.val_min, min(f.val_max, f.start_val + dv)))
            
            # Rotary (Local X)
            f.rotation_var.set(max(f.rot_min, min(f.rot_max, f.start_rot + ldx)))

    @staticmethod
    def _mdp_on_mid_click(event, frame):
        f = MDPInteractionMixin._mdp_get_fader_at(event.x, event.y, frame)
        if f: frame.active_fader = f; f.lift(); f.dragging = True; f.start_x, f.start_y = event.x, event.y; f.start_pos = (f.x, f.y)

    @staticmethod
    def _mdp_on_mid_drag(event, frame):
        f = frame.active_fader
        if f and f.dragging: f.x, f.y = f.start_pos[0] + (event.x - f.start_x), f.start_pos[1] + (event.y - f.start_y); f.render()

    @staticmethod
    def _mdp_on_release(event, frame):
        if frame.active_fader: frame.active_fader.dragging = False; frame.active_fader = None

    @staticmethod
    def _mdp_on_scroll(event, frame):
        f = MDPInteractionMixin._mdp_get_fader_at(event.x, event.y, frame)
        if f:
            delta = 1 if (event.num == 4 or (hasattr(event, "delta") and event.delta > 0)) else -1
            if event.state & 0x0008: f.angle += delta * 3; f.render()
            else:
                curr = float(f.rotation_var.get())
                f.rotation_var.set(max(f.rot_min, min(f.rot_max, curr + delta * 3)))
